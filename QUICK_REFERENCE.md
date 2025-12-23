# YOLO1125 快速參考指南

## 關鍵檔案位置速查表

| 功能 | 檔案 | 行號 |
|-----|------|------|
| **後端主程式** | `/backend/main.py` | 1-1136 |
| 配置設定 | `/backend/config.py` | 1-27 |
| 資料庫連接 | `/backend/database.py` | 1-55 |
| **YOLO 服務** | `/backend/services/yolo_service.py` | 1-143 |
| 模型載入 | `/backend/services/yolo_service.py` | 25-42 |
| YOLO 推論 | `/backend/services/yolo_service.py` | 67-126 |
| **人臉服務** | `/backend/services/face_service.py` | 1-256 |
| 人臉偵測 | `/backend/services/face_service.py` | 55-86 |
| 人臉比對 | `/backend/services/face_service.py` | 88-127 |
| 使用者註冊 | `/backend/services/face_service.py` | 129-212 |
| **購物車** | `/backend/services/cart_service.py` | 1-128 |
| 加入商品 | `/backend/services/cart_service.py` | 23-61 |
| 移除商品 | `/backend/services/cart_service.py` | 63-82 |
| **WebSocket** | `/backend/main.py` | 38-376 |
| 連線管理 | `/backend/main.py` | 40-81 |
| 訊息處理 | `/backend/main.py` | 341-554 |
| 結帳邏輯 | `/backend/main.py` | 264-337 |
| **前端主程式** | `/frontend/static/js/main.js` | 1-657 |
| 應用初始化 | `/frontend/static/js/main.js` | 6-65 |
| 事件處理 | `/frontend/static/js/main.js` | 293-341 |
| **鏡頭管理** | `/frontend/static/js/camera.js` | 1-213 |
| 鏡頭啟動 | `/frontend/static/js/camera.js` | 18-68 |
| 繪製偵測框 | `/frontend/static/js/camera.js` | 131-170 |
| **購物車前端** | `/frontend/static/js/cart.js` | 1-157 |
| 購物車更新 | `/frontend/static/js/cart.js` | 16-68 |
| 結帳流程 | `/frontend/static/js/cart.js` | 94-141 |

---

## 關鍵配置參數

### YOLO 模型設定 (`config.py`)
```python
YOLO_MODEL_PATH = BASE_DIR.parent / "runs" / "detect" / "supermarket_product_detector" / "weights" / "best.pt"
CONFIDENCE_THRESHOLD = 0.8           # 信心度門檻
FACE_MATCH_TOLERANCE = 0.6           # 人臉比對容忍度 (越小越嚴格)
MONGODB_URL = "mongodb://localhost:27017"
DB_NAME = "yolo1125"
```

### 硬體要求
- **YOLO 推論**: ~100-200ms/幀 (GPU) 或 ~500-1000ms/幀 (CPU)
- **人臉偵測**: ~150-300ms (HOG model, CPU)
- **記憶體**: ~1GB 基礎 + 模型

---

## API 端點速查

### WebSocket
```
ws://localhost:8000/ws/{session_id}
```

### 前端發送訊息
```javascript
// 發送影像幀
wsClient.sendFrame(frameData);

// 發送心跳
wsClient.sendPing();

// 移除購物車商品
wsClient.sendCartRemove(itemIndex);
```

### HTTP REST API
```
POST   /api/checkout                    # 結帳
POST   /api/register                    # 使用者註冊
POST   /api/face-login                  # 人臉登入
POST   /api/face-register               # 人臉註冊
GET    /api/products                    # 取得商品列表
GET    /api/user/{user_id}/info         # 取得使用者資訊
GET    /api/user/{user_id}/transactions # 取得交易歷史
GET    /api/health                      # 健康檢查

# 管理員
POST   /api/admin-login                 # 管理員登入
GET    /api/admin/users                 # 所有使用者
GET    /api/admin/stats                 # 統計資料
PUT    /api/admin/user/{user_id}        # 更新使用者
DELETE /api/admin/user/{user_id}        # 刪除使用者
```

---

## 快速啟動

### 1. 環境準備
```bash
# 確保 MongoDB 執行
# 確保 Python 3.8+ 已安裝

cd yolo1125
pip install -r requirements.txt
```

### 2. 啟動後端
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 打開前端
```
http://localhost:8000/login.html
```

---

## 常見問題及解決

### 問題 1: YOLO 模型未找到
**症狀**: `FileNotFoundError: YOLO 模型不存在`
**解決**:
```bash
# 檢查模型路徑
ls -la runs/detect/supermarket_product_detector/weights/best.pt

# 確認路徑配置
cat backend/config.py | grep YOLO_MODEL_PATH
```

### 問題 2: MongoDB 連接失敗
**症狀**: `MongoDB 連線失敗`
**解決**:
```bash
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod

# 驗證連接
mongo --host localhost:27017
```

### 問題 3: WebSocket 連接中斷
**症狀**: 頻繁顯示「未連線」
**解決**:
- 檢查防火牆是否阻止 WebSocket
- 重啟後端應用
- 清除瀏覽器快取

### 問題 4: 鏡頭無法存取
**症狀**: 「❌ 無法存取鏡頭」
**解決**:
```javascript
// 檢查瀏覽器權限
// 允許存取鏡頭

// 檢查 HTTPS 環境（生產環境需要）
// HTTP 本地開發可以存取鏡頭
```

---

## 資料庫操作速查

### 查詢使用者
```javascript
db.users.find({ name: "使用者名稱" })
```

### 查詢交易
```javascript
db.transactions.find({ user_id: ObjectId("...") })
  .sort({ created_at: -1 })
```

### 查詢商品
```javascript
db.products.find({})
db.products.findOne({ yolo_class_id: 0 })
```

### 插入商品
```javascript
db.products.insertOne({
    name: "商品名稱",
    price: 100,
    yolo_class_id: 0,
    yolo_class_name: "class_name"
})
```

---

## 關鍵類別和方法

### YOLOService
```python
service = get_yolo_service()
detections = service.detect(frame)       # 推論
product = service.get_product_by_class_id(class_id)
```

### FaceService
```python
service = get_face_service()
faces = service.detect_faces(frame)      # 偵測人臉
user = service.match_face(face_encoding) # 比對人臉
result = service.register_user(name, phone, encoding, image)
service.update_last_visit(user_id)
```

### CartService
```python
service = get_cart_service()
cart_summary = service.add_item(session_id, product)
cart_summary = service.remove_item(session_id, index)
service.clear_cart(session_id)
is_valid = service.validate_cart(session_id)
```

### 前端類別
```javascript
// 應用主類
app = new App()
app.init()
app.handleCheckout()
app.updateUserDisplay(user)

// 相機管理
camera = new CameraManager('video', 'canvas')
camera.start()
frame = camera.captureFrame()
camera.drawDetections(detections)

// WebSocket 客戶端
wsClient = new WebSocketClient(url)
wsClient.connect()
wsClient.sendFrame(data)
wsClient.on('detections', handler)

// 購物車
cart = new Cart()
cart.update(cartData)
cart.removeItem(index)
cart.checkout()
```

---

## 環境變數

```bash
# MongoDB 配置
MONGODB_URL=mongodb://localhost:27017

# 管理員認證
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

---

## 日誌輸出位置

| 模組 | 輸出 | 級別 |
|-----|------|------|
| YOLO 服務 | stdout | INFO |
| 人臉服務 | stdout | INFO |
| 購物車服務 | stdout | INFO |
| WebSocket | stdout | INFO/DEBUG |
| 前端控制台 | browser console | DEBUG |

**查看日誌**:
```bash
# 後端日誌直接列印到終端
# 搜尋關鍵詞
✅ 成功訊息
❌ 錯誤訊息
⚠️  警告訊息
```

---

## 效能優化建議

### 1. 降低 YOLO 推論時間
```python
# config.py 中增加模型優化
YOLO_MODEL_PATH = "weights/best-half.pt"  # 使用 half-precision
```

### 2. 減少人臉比對延遲
```python
# 使用更快的偵測模型
face_recognition.face_locations(rgb_frame, model='cnn')  # 比 'hog' 快
```

### 3. 優化影像傳輸
```javascript
// camera.js 中降低 JPEG 品質
return this.canvas.toDataURL('image/jpeg', 0.6);  // 從 0.8 降到 0.6
```

---

## 重要提示

1. **會話管理**: 每個使用者有唯一 session_id，不同瀏覽器視為不同使用者
2. **人臉編碼**: 儲存為 128 維向量，無法逆向還原為人臉圖片
3. **購物車狀態**: 存在後端記憶體，刷新頁面後 WebSocket 重連會保持狀態
4. **商品快取**: 系統啟動時從 MongoDB 載入，新增商品需要重啟後端
5. **交��記錄**: 一旦結帳完成，交易記錄永久儲存到 MongoDB，不可更改

---

## 系統檢查清單

啟動前驗証：
- [ ] MongoDB 執行中 (`mongod --version`)
- [ ] Python 3.8+ 安裝 (`python --version`)
- [ ] 依賴套件安裝 (`pip list | grep ultralytics`)
- [ ] YOLO 模型存在 (best.pt ~6.2MB)
- [ ] 前端檔案完整 (index.html, login.html, static/js/)
- [ ] 埠 8000 未被佔用 (`lsof -i :8000`)

執行中驗証：
- [ ] WebSocket 連接成功 (瀏覽器控制台無錯誤)
- [ ] 相機畫面正常顯示
- [ ] YOLO 模型已載入 (日誌顯示類別數量)
- [ ] 人臉服務已載入 (日誌顯示已知人臉數量)
- [ ] MongoDB 連接正常 (健康檢查通過)

