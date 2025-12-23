# YOLO1125 智慧無人商店 - 辨識系統架構分析

## 目錄結構
```
yolo1125/
├── backend/                          # 後端服務
│   ├── main.py                       # FastAPI 主應用
│   ├── config.py                     # 配置文件
│   ├── database.py                   # MongoDB 連接
│   ├── services/
│   │   ├── yolo_service.py          # YOLO 商品偵測服務
│   │   ├── face_service.py          # 人臉識別服務
│   │   └── cart_service.py          # 購物車服務
│   ├── models/                       # 資料模型
│   │   ├── user.py
│   │   ├── product.py
│   │   └── transaction.py
│   └── data/
│       └── faces/                    # 人臉圖片存儲
│
├── frontend/                         # 前端應用
│   ├── index.html                    # 購物頁面
│   ├── login.html                    # 登入頁面
│   ├── admin.html                    # 管理員頁面
│   └── static/js/
│       ├── main.js                   # 應用主邏輯
│       ├── camera.js                 # 鏡頭管理
│       ├── websocket.js              # WebSocket 通訊
│       ├── cart.js                   # 購物車邏輯
│       ├── login.js                  # 登入邏輯
│       └── admin.js                  # 管理頁面邏輯
│
├── scripts/                          # 測試腳本
│   ├── test_yolo.py
│   ├── test_cart.py
│   └── ...
│
└── runs/detect/supermarket_product_detector/
    └── weights/
        └── best.pt                   # YOLO 訓練模型
```

---

## 1. 辨識按鈕的處理邏輯

### 前端按鈕操作 (camera.js + main.js)

**結帳按鈕** (`index.html` 第127行)
```html
<button id="checkout-btn" class="btn-primary" disabled>
    完成結帳
</button>
```

**按鈕事件處理** (main.js 第296-300行)
```javascript
const checkoutBtn = document.getElementById('checkout-btn');
if (checkoutBtn) {
    checkoutBtn.addEventListener('click', () => this.handleCheckout());
}
```

**結帳流程** (cart.js 第94-141行)
1. 驗證購物車非空
2. 確認訊息提示
3. POST `/api/checkout` 請求後端
4. 後端處理完後，WebSocket 返回 `cart_updated` 訊息自動清空購物車

### 後端結帳端點 (main.py 第264-337行)
```python
@app.post("/api/checkout")
async def checkout(data: dict):
    # 1. 驗證 session 和使用者登入狀態
    # 2. 驗證購物車非空
    # 3. 建立交易記錄到 MongoDB
    # 4. 清空購物車
    # 5. 發送 WebSocket 更新訊息
```

---

## 2. 模型載入和推論的程式碼

### YOLO 模型配置 (config.py)

| 設定項 | 值 | 說明 |
|-------|-----|------|
| YOLO_MODEL_PATH | `../runs/detect/supermarket_product_detector/weights/best.pt` | 模型路徑 |
| CONFIDENCE_THRESHOLD | 0.8 | 信心度門檻值 |
| WS_FRAME_RATE | 5 | 每秒處理影格數 |

### YOLO 模型載入 (yolo_service.py 第16-42行)

```python
class YOLOService:
    def __init__(self):
        self.model = None
        self.product_cache = {}  # yolo_class_id -> product_info
        self.load_model()
        self.load_products()
    
    def load_model(self):
        """載入 YOLO 模型"""
        model_path = YOLO_MODEL_PATH
        if not model_path.exists():
            raise FileNotFoundError(f"YOLO 模型不存在: {model_path}")
        
        self.model = YOLO(str(model_path))
        print(f"✅ YOLO 模型載入成功")
        print(f"   類別數量: {len(self.model.names)}")
        print(f"   類別名稱: {self.model.names}")
```

### 推論流程 (yolo_service.py 第67-126行)

```python
def detect(self, frame: np.ndarray) -> List[Dict]:
    """
    偵測影像中的商品
    Returns: 偵測結果 [{
        'class_id': int,
        'class_name': str,
        'confidence': float,
        'bbox': [x1, y1, x2, y2],
        'product': {id, name, price} or None
    }]
    """
    if self.model is None:
        return []
    
    try:
        # YOLO 推論
        results = self.model(frame, verbose=False)
        
        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # 過濾低信心度
                if confidence < CONFIDENCE_THRESHOLD:
                    continue
                
                # 查詢商品資訊
                product = self.product_cache.get(class_id)
                
                detection = {
                    'class_id': class_id,
                    'class_name': self.model.names.get(class_id),
                    'confidence': confidence,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'product': product
                }
                detections.append(detection)
        
        return detections
```

### 商品快取載入 (yolo_service.py 第44-65行)

```python
def load_products(self):
    """從 MongoDB 資料庫載入商品資訊"""
    db = Database.get_db()
    products = db.products.find({})
    
    for product in products:
        yolo_class_id = product.get('yolo_class_id')
        self.product_cache[yolo_class_id] = {
            'id': str(product['_id']),
            'name': product['name'],
            'price': product['price'],
            'yolo_class_name': product.get('yolo_class_name', '')
        }
    
    print(f"✅ 載入 {len(self.product_cache)} 個商品資訊")
```

---

## 3. 購物車功能

### 購物車服務 (cart_service.py)

| 方法 | 功能 | 返回值 |
|-----|------|--------|
| `add_item(session_id, product)` | 加入商品或增加數量 | 購物車摘要 |
| `remove_item(session_id, index)` | 移除指定商品 | 購物車摘要 |
| `get_cart_summary(session_id)` | 取得購物車摘要 | {items, total_quantity, total_amount} |
| `clear_cart(session_id)` | 清空購物車 | 無 |
| `validate_cart(session_id)` | 驗證購物車非空 | bool |

### 前端購物車 UI (cart.js)

```javascript
class Cart {
    constructor() {
        this.items = [];
        this.totalQuantity = 0;
        this.totalAmount = 0;
    }
    
    update(cartData) {
        // 更新購物車資料並重新渲染 UI
    }
    
    removeItem(index) {
        // 發送移除請求到後端 WebSocket
        wsClient.sendCartRemove(index);
    }
    
    async checkout() {
        // POST /api/checkout 進行結帳
    }
}
```

### 購物車流程

1. **YOLO 偵測到商品** → `handle_product_detected()`
2. **加入購物車** → `cart_service.add_item()`
3. **發送 WebSocket 更新** → `cart_updated` 訊息
4. **前端渲染** → `cart.update()` + UI 重繪
5. **移除商品** → WebSocket `cart_remove` 訊息 → 後端處理
6. **結帳** → `/api/checkout` → MongoDB 交易記錄

---

## 4. 前端與後端的互動方式

### 通訊架構

```
前端浏览器 
    ↓
WebSocket (即時通訊) / HTTP REST API
    ↓
FastAPI 後端 (main.py)
    ↓
MongoDB 資料庫
```

### WebSocket 訊息流 (websocket.js + main.py)

**前端發送訊息類型**:
| 訊息類型 | 內容 | 發送者 |
|---------|------|--------|
| `frame` | Base64 編碼的影像 | camera.js (每1秒) |
| `ping` | 心跳信號 | websocket.js |
| `cart_remove` | 移除購物車商品 | cart.js |

**後端發送訊息類型**:
| 訊息類型 | 內容 | 觸發條件 |
|---------|------|----------|
| `user_login` | 使用者資訊 | 人臉識別成功 |
| `detections` | YOLO 偵測結果 | 商品被偵測到 |
| `product_added` | 商品加入購物車 | 商品加入成功 |
| `cart_updated` | 購物車狀態 | 購物車改變 |
| `face_detected` | 人臉偵測結果 | 新人臉被偵測 |
| `face_status` | 人臉狀態 | 定期更新 |

### HTTP REST API 端點

**認證相關**:
```
POST /api/face-login          # 人臉識別登入
POST /api/face-register       # 人臉識別註冊
POST /api/register            # 使用者註冊
POST /api/checkout            # 結帳
```

**資訊查詢**:
```
GET /api/products                           # 取得商品列表
GET /api/user/{user_id}/info               # 取得使用者資訊
GET /api/user/{user_id}/transactions       # 取得交易歷史
GET /api/health                            # 健康檢查
```

**管理員**:
```
POST /api/admin-login                       # 管理員登入
GET /api/admin/users                       # 取得所有使用者
GET /api/admin/stats                       # 取得統計資料
GET /api/admin/user/{user_id}/transactions # 查看使用者交易
PUT /api/admin/user/{user_id}              # 更新使用者資訊
DELETE /api/admin/user/{user_id}           # 刪除使用者
```

### WebSocket 連線管理 (main.py 第40-81行)

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.sessions: Dict[str, dict] = {}  # session_id: {user_id, cart, ...}
    
    async def connect(websocket, session_id)
    def disconnect(session_id)
    async def send_message(session_id, message)
    def get_session(session_id)
```

---

## 5. 識別流程詳解

### A. 人臉識別流程 (face_service.py)

**步驟 1: 人臉偵測** (線上)
```python
def detect_faces(self, frame: np.ndarray):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model='hog')
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    return [(encoding, location), ...]
```

**步驟 2: 人臉比對** (線上)
```python
def match_face(self, face_encoding: np.ndarray):
    # 計算與所有已知人臉的距離
    face_distances = face_recognition.face_distance(
        known_encodings, face_encoding
    )
    best_distance = np.min(face_distances)
    
    # 檢查距離是否在容忍範圍內
    if best_distance < FACE_MATCH_TOLERANCE (0.6):  # 越小越嚴格
        return matched_user
    return None
```

**步驟 3: 使用者註冊** (首次)
```python
def register_user(self, name, phone, face_encoding, face_image):
    # 1. 檢查電話是否已存在
    # 2. 儲存人臉特徵到 MongoDB
    # 3. 儲存人臉圖片到磁盤 (data/faces/{user_id}.jpg)
    # 4. 加入記憶體快取
```

**識別參數配置** (config.py):
```python
FACE_MATCH_TOLERANCE = 0.6  # 容忍度 (0.0-1.0，越小越嚴格)
```

### B. YOLO 商品識別流程

**訊息流**:
```
前端發送影像幀 (WebSocket frame)
    ↓
後端接收 (main.py handle_frame)
    ↓
YOLO 推論 (yolo_service.detect)
    ↓
過濾低信心度 (confidence >= 0.8)
    ↓
查詢商品資訊 (product_cache)
    ↓
發送偵測結果 (WebSocket detections)
    ↓
自動加入購物車 (handle_product_detected)
    ↓
發送購物車更新 (WebSocket cart_updated)
```

**頻率控制** (main.py 第379-440行):
```python
# 商品偵測：最快 0.2 秒處理一次
if current_time - last_time < 0.2:
    return

# 人臉識別：1 秒間隔
if current_time - last_time > 1.0:
    await handle_face_detection(...)
```

---

## 6. 資料流向

### 使用者登入流程

```
1. 啟動應用 (index.html)
   ↓
2. 初始化 (main.js App.init())
   - 啟動相機
   - 連接 WebSocket
   - 開始發送影像幀 (每1秒)
   
3. 後端處理影像
   - handle_frame (主.py 379行)
   - 如果未登入：進行人臉識別
   - 如果已登入：進行YOLO商品偵測
   
4. 人臉識別成功
   - face_service.match_face()
   - 發送 user_login 訊息
   - 更新 session['user_id']
   
5. 前端更新
   - handleUserLogin (main.js 178行)
   - 顯示使用者資訊
   - 啟用結帳按鈕
```

### 商品購物流程

```
1. YOLO 偵測到商品
   - yolo_service.detect()
   - 信心度 >= 0.8
   - 發送 detections 訊息
   
2. 前端繪製偵測框
   - camera.drawDetections()
   
3. 自動加入購物車
   - handle_product_detected (main.py 503行)
   - cart_service.add_item()
   
4. 發送購物車更新
   - WebSocket cart_updated 訊息
   
5. 前端更新 UI
   - cart.update()
   - 重新渲染購物車
   
6. 使用者確認結帳
   - cart.checkout()
   - POST /api/checkout
   
7. 後端處理結帳
   - 驗證購物車
   - 建立交易記錄 (MongoDB)
   - 清空購物車
   - 發送 cart_updated 清空訊息
```

---

## 7. 資料庫結構

### MongoDB Collections

**Users Collection**:
```javascript
{
    _id: ObjectId,
    name: String,
    phone: String (unique index),
    birthday: DateTime (optional),
    face_encoding: Array<Float>,      // 128維特徵向量
    face_image_path: String,
    created_at: DateTime,
    last_visit: DateTime
}
```

**Products Collection**:
```javascript
{
    _id: ObjectId,
    name: String,
    price: Number,
    yolo_class_id: Number (unique index),
    yolo_class_name: String,
    created_at: DateTime
}
```

**Transactions Collection**:
```javascript
{
    _id: ObjectId,
    user_id: ObjectId (indexed),
    user_name: String,
    items: Array<{
        product_id: String,
        name: String,
        unit_price: Number,
        quantity: Number,
        subtotal: Number
    }>,
    total_quantity: Number,
    total_amount: Number,
    created_at: DateTime (indexed)
}
```

---

## 8. 系統啟動流程

### 後端啟動 (main.py 第88-108行)

```python
@app.on_event("startup")
async def startup_event():
    # 1. 連接 MongoDB
    Database.connect()
    
    # 2. 初始化 YOLO 模型 (首次請求時載入)
    get_yolo_service()
    
    # 3. 預先載入人臉服務 (載入所有已知人臉)
    face_service = get_face_service()
    print(f"✅ 人臉服務已載入: {len(face_service.known_faces)} 個已知人臉")
```

### 前端啟動 (main.js 第643-650行)

```javascript
document.addEventListener('DOMContentLoaded', async () => {
    app = new App();
    await app.init();
    // 1. 啟動相機
    // 2. 連接 WebSocket
    // 3. 設定事件監聽
    // 4. 開始發送影像幀
});
```

---

## 9. 模型路徑和配置總結

| 項目 | 路徑/值 | 說明 |
|-----|--------|------|
| YOLO 模型 | `../runs/detect/supermarket_product_detector/weights/best.pt` | 6.2MB 訓練模型 |
| 人臉圖片 | `./data/faces/{user_id}.jpg` | 使用者註冊時儲存 |
| MongoDB | `mongodb://localhost:27017/yolo1125` | 本機開發環境 |
| 前端靜態檔 | `./frontend/static/` | JS/CSS 資源 |
| WebSocket | `ws://localhost:8000/ws/{session_id}` | 即時通訊 |
| REST API | `http://localhost:8000/api/` | HTTP 端點 |

---

## 10. 關鍵特性

### 效能最佳化
- **幀頻控制**: 商品偵測 0.2秒、人臉識別 1秒
- **信心度過濾**: YOLO 偵測 >= 0.8
- **人臉容忍度**: 0.6 (可調整)
- **快取機制**: 商品資訊和已知人臉都在記憶體中

### 即時性
- **WebSocket** 雙向通訊
- **自動加入購物車** (無需按鈕)
- **即時視覺回饋** (偵測框、提示訊息)

### 安全性
- **Session 管理** (唯一 session_id)
- **人臉特徵儲存** (128維向量，不可反轉)
- **管理員帳密** (環境變數 ADMIN_USERNAME/PASSWORD)

---

## 11. 部署指令

```bash
# 啟動後端
cd yolo1125
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 或使用提供的啟動腳本
bash start.sh
```

**必要環境**:
- Python 3.8+
- MongoDB 服務運行
- GPU (建議用於 YOLO ���論，但 CPU 也可運行)

