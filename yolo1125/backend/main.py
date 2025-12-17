"""
YOLO1125 智慧無人商店系統 - FastAPI 主程式
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import base64
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict

from backend.database import Database
from backend.config import BASE_DIR
from backend.services.yolo_service import get_yolo_service
from backend.services.face_service import get_face_service
from backend.services.cart_service import get_cart_service

# 初始化 FastAPI
app = FastAPI(
    title="YOLO1125 智慧無人商店",
    description="結合 YOLO 物品辨識與人臉識別的智慧結帳系統",
    version="1.0.0"
)

# CORS 設定（本地開發）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 連線管理 ====================

class ConnectionManager:
    """WebSocket 連線管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.sessions: Dict[str, dict] = {}  # session_id: {user_id, cart, ...}

    async def connect(self, websocket: WebSocket, session_id: str):
        """接受新的 WebSocket 連線"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.sessions[session_id] = {
            "user_id": None,
            "cart": [],
            "connected_at": datetime.utcnow()
        }
        print(f"✅ WebSocket 連線: {session_id}")

    def disconnect(self, session_id: str):
        """斷開連線"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.sessions:
            del self.sessions[session_id]
        print(f"❌ WebSocket 斷線: {session_id}")

    async def send_message(self, session_id: str, message: dict):
        """發送訊息給特定 session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"❌ 發送訊息失敗: {e}")

    def get_session(self, session_id: str):
        """取得 session 資料"""
        return self.sessions.get(session_id)

# 全域連線管理器
manager = ConnectionManager()

# 記錄最後處理時間（避免過度處理）
last_frame_time: Dict[str, float] = {}
last_face_detection_time: Dict[str, float] = {}

# ==================== 應用程式生命週期 ====================

@app.on_event("startup")
async def startup_event():
    """應用程式啟動時初始化"""
    print("=" * 60)
    print("🚀 啟動 YOLO1125 智慧無人商店系統...")
    print("=" * 60)

    try:
        # 連接資料庫
        Database.connect()

        # 預先載入人臉服務（確保已知人臉被載入）
        face_service = get_face_service()
        print(f"✅ 人臉服務已載入: {len(face_service.known_faces)} 個已知人臉")

        print("✅ 系統啟動完成")
        print(f"✅ 訪問網址: http://localhost:8000")
        print("=" * 60)
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """應用程式關閉時清理資源"""
    print("\n" + "=" * 60)
    print("🛑 關閉系統...")
    Database.close()
    print("✅ 系統已關閉")
    print("=" * 60)

# ==================== HTTP 路由 ====================

@app.get("/")
async def root():
    """重定向到登入頁面"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login.html")

@app.get("/login.html", response_class=HTMLResponse)
async def login_page():
    """提供登入頁面"""
    html_path = BASE_DIR / "frontend" / "login.html"

    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    else:
        return HTMLResponse(
            content="<h1>登入頁面不存在</h1>",
            status_code=404
        )

@app.get("/index.html", response_class=HTMLResponse)
async def shop_page():
    """提供購物頁面"""
    html_path = BASE_DIR / "frontend" / "index.html"

    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    else:
        return HTMLResponse(
            content="<h1>購物頁面不存在</h1>",
            status_code=404
        )

@app.get("/admin.html", response_class=HTMLResponse)
async def admin_page():
    """提供管理者頁面"""
    html_path = BASE_DIR / "frontend" / "admin.html"

    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    else:
        return HTMLResponse(
            content="<h1>管理者頁面不存在</h1>",
            status_code=404
        )

@app.get("/api/products")
async def get_products():
    """取得商品列表"""
    try:
        db = Database.get_db()
        products_cursor = db.products.find({}, {"_id": 0})

        # 轉換 datetime 為字串
        products = []
        for p in products_cursor:
            if 'created_at' in p:
                p['created_at'] = p['created_at'].isoformat()
            products.append(p)

        return JSONResponse(content={
            "success": True,
            "products": products,
            "count": len(products)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得商品失敗: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康檢查端點"""
    try:
        db = Database.get_db()
        # 測試資料庫連線
        products_count = db.products.count_documents({})

        return JSONResponse(content={
            "status": "healthy",
            "database": "connected",
            "products": products_count,
            "active_connections": len(manager.active_connections)
        })
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.post("/api/register")
async def register_user(data: dict):
    """註冊新使用者"""
    try:
        session_id = data.get("session_id")
        name = data.get("name")
        phone = data.get("phone")

        if not all([session_id, name, phone]):
            raise HTTPException(status_code=400, detail="缺少必要欄位")

        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=400, detail="Session 不存在")

        pending_face = session.get('pending_face')
        if not pending_face:
            raise HTTPException(status_code=400, detail="找不到待註冊的人臉")

        # 註冊使用者
        face_service = get_face_service()
        user = face_service.register_user(
            name=name,
            phone=phone,
            face_encoding=pending_face['encoding'],
            face_image=pending_face['image']
        )

        # 自動登入
        session['user_id'] = user['id']
        del session['pending_face']

        # 發送登入訊息至 WebSocket
        await manager.send_message(session_id, {
            "type": "user_login",
            "user": user,
            "is_new": True
        })

        return JSONResponse(content={
            "success": True,
            "user": user
        })

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"註冊失敗: {str(e)}")

@app.post("/api/checkout")
async def checkout(data: dict):
    """處理結帳"""
    try:
        session_id = data.get("session_id")

        if not session_id:
            raise HTTPException(status_code=400, detail="缺少 session_id")

        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=400, detail="Session 不存在")

        user_id = session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="使用者未登入")

        # 驗證購物車
        cart_service = get_cart_service()
        if not cart_service.validate_cart(session_id):
            raise HTTPException(status_code=400, detail="購物車是空的")

        # 取得購物車資料
        cart_summary = cart_service.get_cart_summary(session_id)

        # 取得使用者資訊
        face_service = get_face_service()
        user = face_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=400, detail="使用者不存在")

        # 建立交易記錄
        from bson import ObjectId
        transaction = {
            "user_id": ObjectId(user_id),
            "user_name": user['name'],
            "items": cart_summary['items'],
            "total_quantity": cart_summary['total_quantity'],
            "total_amount": cart_summary['total_amount'],
            "created_at": datetime.utcnow()
        }

        db = Database.get_db()
        result = db.transactions.insert_one(transaction)
        transaction_id = str(result.inserted_id)

        # 清空購物車
        cart_service.clear_cart(session_id)

        # 發送購物車更新（清空）
        await manager.send_message(session_id, {
            "type": "cart_updated",
            "cart": {
                "items": [],
                "total_quantity": 0,
                "total_amount": 0
            }
        })

        print(f"✅ 結帳成功: {user['name']} - NT$ {cart_summary['total_amount']}")

        return JSONResponse(content={
            "success": True,
            "message": "結帳成功",
            "transaction_id": transaction_id,
            "total_amount": cart_summary['total_amount']
        })

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"結帳失敗: {str(e)}")

# ==================== WebSocket 路由 ====================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 端點處理即時通訊"""
    await manager.connect(websocket, session_id)

    try:
        while True:
            # 接收訊息
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "frame":
                # 處理影像影格
                await handle_frame(session_id, data)

            elif message_type == "ping":
                # 心跳檢測
                await manager.send_message(session_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif message_type == "cart_remove":
                # 移除購物車商品（Task 006 會實作）
                await handle_cart_remove(session_id, data)

            else:
                print(f"⚠️ 未知訊息類型: {message_type}")

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"🔌 WebSocket 正常斷線: {session_id}")
    except Exception as e:
        print(f"❌ WebSocket 錯誤: {e}")
        manager.disconnect(session_id)

# ==================== 訊息處理函式 ====================

async def handle_frame(session_id: str, data: dict):
    """處理影像影格"""
    try:
        # 檢查處理頻率（避免過度處理）
        current_time = datetime.utcnow().timestamp()
        last_time = last_frame_time.get(session_id, 0)

        if current_time - last_time < 0.2:  # 最快 0.2 秒處理一次
            return

        last_frame_time[session_id] = current_time

        # 解碼 Base64 影像
        frame_data = data.get("frame")
        if not frame_data:
            return

        # 移除 data:image/jpeg;base64, 前綴
        if "," in frame_data:
            frame_data = frame_data.split(",")[1]

        # Base64 解碼
        image_bytes = base64.b64decode(frame_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            print("⚠️ 影像解碼失敗")
            return

        session = manager.get_session(session_id)

        # Task 005: 人臉識別（僅在未登入時執行）
        if not session.get('user_id'):
            current_time = datetime.utcnow().timestamp()
            last_time = last_face_detection_time.get(session_id, 0)

            if current_time - last_time > 1.0:  # 1 秒間隔
                last_face_detection_time[session_id] = current_time
                await handle_face_detection(session_id, frame)

        # Task 004: YOLO 商品偵測（僅在已登入時執行）
        elif session.get('user_id'):
            yolo_service = get_yolo_service()
            detections = yolo_service.detect(frame)

            if detections:
                # 發送偵測結果至前端
                await manager.send_message(session_id, {
                    "type": "detections",
                    "detections": detections,
                    "timestamp": datetime.utcnow().isoformat()
                })

                # 如果偵測到商品，發送商品偵測事件
                for detection in detections:
                    product = detection.get('product')
                    if product:
                        await handle_product_detected(session_id, product, detection)

    except Exception as e:
        print(f"❌ 處理影格錯誤: {e}")

async def handle_face_detection(session_id: str, frame: np.ndarray):
    """處理人臉偵測"""
    try:
        face_service = get_face_service()
        faces = face_service.detect_faces(frame)

        if not faces:
            # 發送未偵測到人臉的訊息
            await manager.send_message(session_id, {
                "type": "face_status",
                "detected": False
            })
            return

        # 取第一張臉
        face_encoding, face_location = faces[0]
        top, right, bottom, left = face_location

        # 嘗試比對
        matched_user = face_service.match_face(face_encoding)

        if matched_user:
            # 找到已知使用者，自動登入
            session = manager.get_session(session_id)
            session['user_id'] = matched_user['id']

            await manager.send_message(session_id, {
                "type": "user_login",
                "user": matched_user,
                "is_new": False,
                "bbox": [left, top, right, bottom]
            })

            print(f"✅ 使用者登入: {matched_user['name']}")

        else:
            # 新使用者，請求註冊
            # 裁切人臉圖片
            face_image = frame[top:bottom, left:right]

            # 暫存人臉資料
            session = manager.get_session(session_id)
            session['pending_face'] = {
                'encoding': face_encoding,
                'image': face_image,
                'location': [left, top, right, bottom]
            }

            await manager.send_message(session_id, {
                "type": "face_detected",
                "action": "register_prompt",
                "bbox": [left, top, right, bottom]
            })

            print(f"👤 偵測到新人臉，等待註冊")

    except Exception as e:
        print(f"❌ 人臉偵測處理錯誤: {e}")
        import traceback
        traceback.print_exc()

async def handle_product_detected(session_id: str, product: dict, detection: dict):
    """處理偵測到的商品"""
    try:
        session = manager.get_session(session_id)

        if not session or not session.get('user_id'):
            # 使用者未登入，不加入購物車
            return

        # Task 006: 加入購物車
        cart_service = get_cart_service()
        cart_summary = cart_service.add_item(session_id, product)

        # 發送購物車更新
        await manager.send_message(session_id, {
            "type": "cart_updated",
            "cart": cart_summary
        })

        # 發送商品加入事件（用於視覺回饋）
        await manager.send_message(session_id, {
            "type": "product_added",
            "product": product,
            "confidence": detection['confidence']
        })

        print(f"📦 商品加入購物車: {product['name']} (信心度: {detection['confidence']:.2f})")

    except Exception as e:
        print(f"❌ 處理商品偵測錯誤: {e}")

async def handle_cart_remove(session_id: str, data: dict):
    """處理移除購物車商品"""
    try:
        item_index = data.get("index")

        if item_index is None:
            print("⚠️ 缺少商品索引")
            return

        # Task 006: 移除購物車商品
        cart_service = get_cart_service()
        cart_summary = cart_service.remove_item(session_id, item_index)

        # 發送更新
        await manager.send_message(session_id, {
            "type": "cart_updated",
            "cart": cart_summary
        })

    except Exception as e:
        print(f"❌ 處理移除請求錯誤: {e}")

# ==================== 錯誤處理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """全域錯誤處理"""
    print(f"❌ 錯誤: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc)
        }
    )

# ==================== 人臉登入/註冊 API ====================

@app.post("/api/face-login")
async def face_login(data: dict):
    """
    人臉識別登入
    """
    try:
        image_data = data.get("image")
        session_id = data.get("session_id")

        if not image_data or not session_id:
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 解碼 base64 圖片
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="無法解析圖片")

        # 使用 face_service 進行人臉識別
        face_service = get_face_service()
        faces = face_service.detect_faces(frame)

        if not faces:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "未偵測到人臉，請重試"
                }
            )

        # 取第一張人臉進行比對
        face_encoding, face_location = faces[0]
        user = face_service.match_face(face_encoding)

        if user:
            # 找到匹配的使用者
            user_id = user['id']  # match_face() 返回的是 'id' 不是 '_id'

            # 更新 session
            if session_id not in manager.sessions:
                manager.sessions[session_id] = {}

            manager.sessions[session_id]['user_id'] = user_id
            manager.sessions[session_id]['user_name'] = user['name']

            # 更新最後訪問時間
            face_service.update_last_visit(user_id)

            # 獲取用戶頭像
            face_image_base64 = None
            try:
                face_image_path = Path(__file__).parent / "data" / "faces" / f"{user_id}.jpg"
                if face_image_path.exists():
                    with open(face_image_path, 'rb') as f:
                        face_image_base64 = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                print(f"❌ 讀取頭像失敗: {e}")

            return JSONResponse(
                content={
                    "success": True,
                    "message": "登入成功",
                    "user": {
                        "id": user_id,
                        "name": user['name'],
                        "phone": user.get('phone', ''),
                        "avatar": f"data:image/jpeg;base64,{face_image_base64}" if face_image_base64 else None
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "未識別到註冊使用者，請先註冊"
                }
            )

    except HTTPException as exc:
        raise exc
    except Exception as exc:
        print(f"❌ 人臉登入錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/face-register")
async def face_register(data: dict):
    """
    人臉識別註冊
    """
    try:
        name = data.get("name")
        phone = data.get("phone")
        birthday = data.get("birthday")
        image_data = data.get("image")
        session_id = data.get("session_id")

        if not all([name, phone, birthday, image_data, session_id]):
            raise HTTPException(status_code=400, detail="缺少必要參數")

        # 解碼 base64 圖片
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="無法解析圖片")

        # 使用 face_service 偵測人臉
        face_service = get_face_service()
        faces = face_service.detect_faces(frame)

        if not faces:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "未偵測到人臉，請重新拍攝"
                }
            )

        # 取第一張人臉進行註冊
        face_encoding, face_location = faces[0]
        top, right, bottom, left = face_location

        # 裁切人臉圖片
        face_image = frame[top:bottom, left:right]

        # 註冊使用者
        user_data = face_service.register_user(name, phone, face_encoding, face_image, birthday)

        if not user_data:
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "message": "註冊失敗，請重試"
                }
            )

        user_id = user_data.get('id') or str(user_data.get('_id'))

        # 更新 session
        if session_id not in manager.sessions:
            manager.sessions[session_id] = {}

        manager.sessions[session_id]['user_id'] = user_id
        manager.sessions[session_id]['user_name'] = name

        # 獲取用戶頭像
        face_image_base64 = None
        try:
            face_image_path = Path(__file__).parent / "data" / "faces" / f"{user_id}.jpg"
            if face_image_path.exists():
                with open(face_image_path, 'rb') as f:
                    face_image_base64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ 讀取頭像失敗: {e}")

        return JSONResponse(
            content={
                "success": True,
                "message": "註冊成功",
                "user": {
                    "id": user_id,
                    "name": name,
                    "phone": phone,
                    "birthday": birthday,
                    "avatar": f"data:image/jpeg;base64,{face_image_base64}" if face_image_base64 else None
                }
            }
        )

    except HTTPException as exc:
        raise exc
    except Exception as exc:
        print(f"❌ 人臉註冊錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/user/{user_id}/transactions")
async def get_user_transactions(user_id: str):
    """
    獲取使用者交易歷史
    """
    try:
        from bson import ObjectId
        db = Database.get_db()

        # 查詢該使用者的所有交易記錄
        transactions = list(db.transactions.find(
            {"user_id": ObjectId(user_id)}
        ).sort("created_at", -1))

        # 計算統計資料
        total_transactions = len(transactions)
        total_spent = sum(t.get('total_amount', 0) for t in transactions)

        # 格式化交易記錄
        formatted_transactions = []
        for t in transactions:
            formatted_transactions.append({
                "id": str(t['_id']),
                "date": t['created_at'].isoformat() if t.get('created_at') else "",
                "items": t.get('items', []),
                "total_quantity": t.get('total_quantity', 0),
                "total_amount": t.get('total_amount', 0)
            })

        return JSONResponse(
            content={
                "success": True,
                "total_transactions": total_transactions,
                "total_spent": total_spent,
                "transactions": formatted_transactions
            }
        )

    except Exception as exc:
        print(f"❌ 獲取交易歷史錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/user/{user_id}/info")
async def get_user_info(user_id: str):
    """
    獲取使用者詳細資訊
    """
    try:
        from bson import ObjectId
        db = Database.get_db()

        user = db.users.find_one({"_id": ObjectId(user_id)})

        if not user:
            raise HTTPException(status_code=404, detail="使用者不存在")

        # 獲取用戶頭像
        face_image_base64 = None
        try:
            face_image_path = Path(__file__).parent / "data" / "faces" / f"{user_id}.jpg"
            if face_image_path.exists():
                with open(face_image_path, 'rb') as f:
                    face_image_base64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ 讀取頭像失敗: {e}")

        return JSONResponse(
            content={
                "success": True,
                "user": {
                    "id": str(user['_id']),
                    "name": user.get('name', ''),
                    "phone": user.get('phone', ''),
                    "birthday": user.get('birthday', '').isoformat() if user.get('birthday') else "",
                    "created_at": user.get('created_at', '').isoformat() if user.get('created_at') else "",
                    "last_visit": user.get('last_visit', '').isoformat() if user.get('last_visit') else "",
                    "avatar": f"data:image/jpeg;base64,{face_image_base64}" if face_image_base64 else None
                }
            }
        )

    except HTTPException as exc:
        raise exc
    except Exception as exc:
        print(f"❌ 獲取使用者資訊錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ==================== 管理者 API ====================

@app.post("/api/admin-login")
async def admin_login(data: dict):
    """
    管理者登入
    """
    try:
        from backend.config import ADMIN_USERNAME, ADMIN_PASSWORD

        username = data.get('username', '')
        password = data.get('password', '')

        if not username or not password:
            raise HTTPException(status_code=400, detail="請輸入帳號和密碼")

        # 驗證管理者帳號密碼
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return JSONResponse(
                content={
                    "success": True,
                    "message": "管理者登入成功"
                }
            )
        else:
            raise HTTPException(status_code=401, detail="帳號或密碼錯誤")

    except HTTPException:
        raise
    except Exception as exc:
        print(f"❌ 管理者登入錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/admin/users")
async def get_all_users():
    """
    獲取所有使用者列表
    """
    try:
        from bson import ObjectId
        db = Database.get_db()

        users = list(db.users.find({}))

        # 為每個使用者獲取交易統計
        user_list = []
        for user in users:
            user_id = str(user['_id'])

            # 計算累積消費
            transactions = list(db.transactions.find({"user_id": ObjectId(user_id)}))
            total_spent = sum(t.get('total_amount', 0) for t in transactions)

            # 獲取頭像
            face_image_base64 = None
            try:
                face_image_path = Path(__file__).parent / "data" / "faces" / f"{user_id}.jpg"
                if face_image_path.exists():
                    with open(face_image_path, 'rb') as f:
                        face_image_base64 = base64.b64encode(f.read()).decode('utf-8')
            except:
                pass

            user_list.append({
                "id": user_id,
                "name": user.get('name', ''),
                "phone": user.get('phone', ''),
                "birthday": user.get('birthday', '').isoformat() if user.get('birthday') else "",
                "created_at": user.get('created_at', '').isoformat() if user.get('created_at') else "",
                "last_visit": user.get('last_visit', '').isoformat() if user.get('last_visit') else "",
                "total_spent": total_spent,
                "avatar": f"data:image/jpeg;base64,{face_image_base64}" if face_image_base64 else None
            })

        return JSONResponse(
            content={
                "success": True,
                "users": user_list,
                "count": len(user_list)
            }
        )

    except Exception as exc:
        print(f"❌ 獲取使用者列表錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/admin/stats")
async def get_admin_stats():
    """
    獲取管理統計資料
    """
    try:
        from bson import ObjectId
        db = Database.get_db()

        # 總使用者數
        total_users = db.users.count_documents({})

        # 總交易數和總營業額
        transactions = list(db.transactions.find({}))
        total_transactions = len(transactions)
        total_revenue = sum(t.get('total_amount', 0) for t in transactions)

        return JSONResponse(
            content={
                "success": True,
                "stats": {
                    "total_users": total_users,
                    "total_transactions": total_transactions,
                    "total_revenue": total_revenue
                }
            }
        )

    except Exception as exc:
        print(f"❌ 獲取統計資料錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/admin/user/{user_id}/transactions")
async def get_user_transactions(user_id: str):
    """
    獲取特定使用者的交易記錄
    """
    try:
        from bson import ObjectId
        db = Database.get_db()

        # 驗證使用者存在
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="使用者不存在")

        # 查詢交易記錄，按時間倒序排列
        transactions = list(db.transactions.find(
            {"user_id": ObjectId(user_id)}
        ).sort("created_at", -1))

        # 計算統計資料
        total_amount = sum(t.get('total_amount', 0) for t in transactions)
        total_count = len(transactions)
        total_items = sum(t.get('total_quantity', 0) for t in transactions)

        # 格式化交易記錄
        formatted_transactions = []
        for t in transactions:
            formatted_transactions.append({
                "id": str(t['_id']),
                "created_at": t['created_at'].isoformat(),
                "items": t.get('items', []),
                "total_quantity": t.get('total_quantity', 0),
                "total_amount": t.get('total_amount', 0)
            })

        return JSONResponse(
            content={
                "success": True,
                "transactions": formatted_transactions,
                "summary": {
                    "total_amount": total_amount,
                    "total_count": total_count,
                    "total_items": total_items
                }
            }
        )

    except Exception as exc:
        print(f"❌ 獲取交易記錄錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.put("/api/admin/user/{user_id}")
async def update_user(user_id: str, data: dict):
    """
    更新使用者資訊
    """
    try:
        from bson import ObjectId
        db = Database.get_db()

        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="使用者不存在")

        # 準備更新資料
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'phone' in data:
            update_data['phone'] = data['phone']
        if 'birthday' in data and data['birthday']:
            try:
                update_data['birthday'] = datetime.fromisoformat(data['birthday'].replace('Z', '+00:00'))
            except:
                try:
                    update_data['birthday'] = datetime.strptime(data['birthday'], '%Y-%m-%d')
                except:
                    pass

        # 更新資料庫
        if update_data:
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )

        # 如果姓名或電話變更，需要更新記憶體中的資料
        if 'name' in update_data:
            face_service = get_face_service()
            if user_id in face_service.known_users:
                face_service.known_users[user_id]['name'] = update_data['name']

        return JSONResponse(
            content={
                "success": True,
                "message": "使用者資訊已更新"
            }
        )

    except HTTPException as exc:
        raise exc
    except Exception as exc:
        print(f"❌ 更新使用者錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/api/admin/user/{user_id}")
async def delete_user(user_id: str):
    """
    刪除使用者
    """
    try:
        from bson import ObjectId
        import os
        db = Database.get_db()

        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="使用者不存在")

        # 刪除使用者資料
        db.users.delete_one({"_id": ObjectId(user_id)})

        # 刪除人臉圖片
        try:
            face_image_path = Path(__file__).parent / "data" / "faces" / f"{user_id}.jpg"
            if face_image_path.exists():
                os.remove(face_image_path)
        except Exception as e:
            print(f"⚠️ 刪除人臉圖片失敗: {e}")

        # 從記憶體中移除
        face_service = get_face_service()
        if user_id in face_service.known_faces:
            del face_service.known_faces[user_id]
        if user_id in face_service.known_users:
            del face_service.known_users[user_id]

        print(f"✅ 使用者已刪除: {user.get('name')} ({user_id})")

        return JSONResponse(
            content={
                "success": True,
                "message": "使用者已刪除"
            }
        )

    except HTTPException as exc:
        raise exc
    except Exception as exc:
        print(f"❌ 刪除使用者錯誤: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

# ==================== 靜態檔案 ====================

# 掛載靜態檔案（如果存在）
static_dir = BASE_DIR / "frontend" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ==================== 主程式入口 ====================

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
