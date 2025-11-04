---
name: yolo1125
status: backlog
created: 2025-10-30T04:03:19Z
progress: 0%
prd: .claude/prds/yolo1125.md
github: [Will be updated when synced to GitHub]
---

# Epic: yolo1125 - 智慧無人商店結帳系統

## Overview

本 Epic 實作一個整合 YOLO 物品辨識與人臉識別的智慧結帳系統，使用已訓練的 YOLOv8 模型（元翠茶、分解茶）結合人臉識別技術，建立無人商店自動結帳解決方案。

**技術重點**：
- 利用現有 YOLO 訓練模型（位於 `runs/` 目錄）
- FastAPI 後端 + 原生 HTML/JS 前端（簡化架構）
- MongoDB 本地資料庫（Users, Products, Transactions）
- WebSocket 實現即時通訊
- OpenCV + face_recognition 處理人臉識別

## Architecture Decisions

### 1. Web 框架：FastAPI
**選擇原因**：
- 內建 WebSocket 支援，適合即時視訊串流
- 現代化、高效能的非同步框架
- 自動生成 API 文件（方便測試）
- 與 OpenCV/YOLO 整合良好

### 2. 人臉識別：face_recognition
**選擇原因**：
- 基於 dlib，準確度高（> 99%）
- API 簡單易用，快速上線
- 直接支援人臉特徵編碼和比對
- 成熟穩定的開源專案

### 3. 前端：純 HTML/CSS/JavaScript
**選擇原因**：
- 無需額外框架，降低複雜度
- 快速開發，符合本地運行需求
- WebRTC getUserMedia 原生支援鏡頭存取
- Canvas API 直接繪製偵測框

### 4. 即時通訊：WebSocket
**選擇原因**：
- 雙向即時通訊，適合視訊串流
- 低延遲，滿足 < 1 秒回應需求
- FastAPI 內建支援

### 5. 資料儲存：MongoDB + 本地檔案
**選擇原因**：
- MongoDB：結構彈性，適合使用者資料和交易記錄
- 本地檔案：人臉圖片儲存在 `data/faces/` 目錄
- 避免 Base64 增加資料庫負擔

### 6. 專案結構：模組化設計
```
yolo1125/
├── backend/
│   ├── main.py              # FastAPI 主程式
│   ├── models/              # 資料模型
│   │   ├── user.py
│   │   ├── product.py
│   │   └── transaction.py
│   ├── services/            # 業務邏輯
│   │   ├── face_service.py  # 人臉識別
│   │   ├── yolo_service.py  # YOLO 辨識
│   │   └── cart_service.py  # 購物車
│   ├── database.py          # MongoDB 連線
│   └── config.py            # 設定檔
├── frontend/
│   ├── index.html           # 主頁面
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── camera.js    # 鏡頭處理
│   │       ├── websocket.js # WebSocket 通訊
│   │       └── cart.js      # 購物車 UI
├── data/
│   └── faces/               # 人臉圖片
├── runs/                    # YOLO 模型（已存在）
├── requirements.txt
└── README.md
```

## Technical Approach

### Frontend Components

#### 1. 鏡頭介面（camera.js）
- **功能**：WebRTC 存取鏡頭，Canvas 顯示畫面
- **關鍵技術**：
  - `navigator.mediaDevices.getUserMedia()` 取得影像串流
  - 定期擷取影格傳送至後端（每 200ms）
  - 在 Canvas 上繪製 YOLO/人臉偵測框

#### 2. WebSocket 通訊（websocket.js）
- **功能**：前後端即時雙向通訊
- **訊息類型**：
  - `frame`：影像影格（Base64）
  - `face_detected`：人臉識別結果
  - `product_detected`：商品識別結果
  - `cart_update`：購物車更新

#### 3. 購物車 UI（cart.js）
- **功能**：顯示商品清單、總價、移除按鈕
- **狀態管理**：簡單 JavaScript 物件
  ```js
  const cart = {
    items: [{product_id, name, quantity, price}],
    total: 0
  }
  ```

#### 4. 主介面（index.html）
- **佈局**：三欄式 Flexbox 設計
  - 左：使用者資訊卡片
  - 中：Canvas 鏡頭畫面
  - 右：購物車清單
  - 底部：「完成結帳」按鈕

### Backend Services

#### 1. FastAPI 主程式（main.py）
- **端點**：
  - `GET /`：提供前端 HTML
  - `WebSocket /ws`：影像處理和即時通訊
  - `POST /api/checkout`：結帳處理
  - `GET /api/products`：商品列表

#### 2. 人臉識別服務（face_service.py）
- **功能**：
  - `detect_face(frame)` → 偵測人臉位置
  - `encode_face(face_image)` → 提取 128-d 特徵向量
  - `match_face(encoding)` → 比對資料庫中的使用者
  - `register_user(name, phone, face_image)` → 註冊新使用者
- **資料流**：
  ```
  影格 → 偵測人臉 → 提取特徵 → 比對資料庫
                                 ├─ 找到 → 回傳使用者資料
                                 └─ 未找到 → 提示註冊
  ```

#### 3. YOLO 辨識服務（yolo_service.py）
- **功能**：
  - 載入訓練好的模型（`runs/detect/train/weights/best.pt`）
  - `detect_products(frame)` → 偵測商品並回傳類別 ID、信心度、座標
  - 過濾低信心度結果（< 0.7）
- **最佳化**：
  - 調整輸入尺寸（640x640 → 480x480 提升速度）
  - 使用 GPU 加速（如可用）

#### 4. 購物車服務（cart_service.py）
- **功能**：
  - `add_item(session_id, product_id)` → 加入商品
  - `remove_item(session_id, item_index)` → 移除商品
  - `get_cart(session_id)` → 取得購物車
  - `checkout(session_id, user_id)` → 結帳並儲存交易
- **狀態管理**：使用 Python dict 暫存各 session 購物車

#### 5. 資料模型（models/）
- **User**：姓名、電話、人臉特徵、圖片路徑
- **Product**：名稱、價格、YOLO 類別 ID
- **Transaction**：使用者 ID、商品清單、總金額、時間

### Infrastructure

#### 1. MongoDB 設定
- **Collections**：
  - `users`：索引 `face_encoding`（近似搜尋）
  - `products`：索引 `yolo_class_id`
  - `transactions`：索引 `user_id` 和 `created_at`

#### 2. 初始資料（MongoDB 腳本）
```python
# scripts/init_db.py
products = [
    {"name": "元翠茶", "price": 150, "yolo_class_id": 0, "yolo_class_name": "yuancui"},
    {"name": "分解茶", "price": 200, "yolo_class_id": 1, "yolo_class_name": "fenjie"}
]
db.products.insert_many(products)
```

#### 3. 環境配置（config.py）
```python
MONGODB_URL = "mongodb://localhost:27017"
DB_NAME = "yolo1125"
YOLO_MODEL_PATH = "runs/detect/train/weights/best.pt"
FACE_IMAGES_DIR = "data/faces"
CONFIDENCE_THRESHOLD = 0.7
```

#### 4. 本地部署
- **啟動步驟**：
  1. 安裝 MongoDB 並啟動服務
  2. `pip install -r requirements.txt`
  3. `python scripts/init_db.py`（初始化商品資料）
  4. `python backend/main.py`
  5. 瀏覽器開啟 `http://localhost:8000`

## Implementation Strategy

### 開發階段（簡化至 3 階段）

#### Phase 1: 核心基礎（Week 1）
整合現有 YOLO 模型和建立基本架構。
- 建立專案結構
- MongoDB 設定和初始資料
- FastAPI 基本端點
- HTML 頁面和 WebSocket 連線
- YOLO 模型載入和測試

**驗收**：能在網頁顯示鏡頭畫面，YOLO 偵測商品並在 Canvas 顯示框

---

#### Phase 2: 人臉識別與購物車（Week 2）
實作使用者識別和購物流程。
- 人臉偵測、註冊、比對
- 購物車邏輯（新增、移除、計價）
- 前端購物車 UI
- 使用者資料顯示

**驗收**：完整購物流程（登入 → 掃商品 → 加入購物車 → 移除商品）

---

#### Phase 3: 結帳與優化（Week 3）
完成結帳功能和效能調校。
- 結帳 API 和交易記錄
- UI/UX 優化（載入動畫、錯誤提示）
- 效能調校（模型推論速度、WebSocket 頻寬）
- 測試和 Bug 修復

**驗收**：完整系統測試，符合 PRD 所有功能和效能要求

### 風險緩解

**風險 1：YOLO 模型路徑錯誤**
- **緩解**：啟動時驗證模型檔案存在，提供清楚錯誤訊息

**風險 2：人臉識別效能不足**
- **緩解**：
  - 降低人臉偵測頻率（每 500ms 而非每影格）
  - 僅在未登入時執行人臉識別

**風險 3：WebSocket 斷線**
- **緩解**：前端自動重連機制

### 測試方法

**單元測試**：
- `face_service.py`：人臉編碼、比對邏輯
- `cart_service.py`：購物車計算
- `yolo_service.py`：模型載入和偵測

**整合測試**：
- WebSocket 影像傳輸
- 完整購物流程
- MongoDB 資料正確性

**效能測試**：
- 人臉識別回應時間 < 2s
- YOLO 偵測回應時間 < 1s
- WebSocket 延遲 < 100ms

## Task Breakdown Preview

將開發工作濃縮為 **8 個核心任務**：

### Phase 1: 核心基礎
- [ ] **Task 1**: 建立專案結構、MongoDB 設定與初始資料
- [ ] **Task 2**: 實作 FastAPI 主程式與 WebSocket 通訊
- [ ] **Task 3**: 建立前端頁面（HTML/CSS）與鏡頭存取

### Phase 2: AI 整合
- [ ] **Task 4**: 整合 YOLO 模型並實作商品偵測服務
- [ ] **Task 5**: 實作人臉識別服務（註冊、比對、登入）

### Phase 3: 業務邏輯
- [ ] **Task 6**: 實作購物車邏輯與前端 UI
- [ ] **Task 7**: 實作結帳流程與交易記錄

### Phase 4: 優化與測試
- [ ] **Task 8**: 系統整合測試、效能優化與 Bug 修復

**總任務數**：8 項（符合簡化要求）

## Dependencies

### 外部依賴

**Python 套件**（requirements.txt）：
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
websockets==12.0
pymongo==4.6.0
opencv-python==4.8.1.78
face-recognition==1.3.0
ultralytics==8.0.220
pillow==10.1.0
numpy==1.24.3
```

**系統依賴**：
- MongoDB 6.0+（本地安裝）
- Python 3.8+
- 電腦鏡頭

**現有資源**：
- ✅ YOLO 訓練模型（`runs/` 目錄）
- ✅ 資料集配置（`dataset/dataset.yaml`）

### 內部依賴順序

```
Task 1 (基礎架構)
  ↓
Task 2 (FastAPI + WebSocket) ──┐
  ↓                             │
Task 3 (前端頁面) ───────────────┤
  ↓                             │
Task 4 (YOLO 整合) ──────────────┤
  ↓                             │
Task 5 (人臉識別) ───────────────┤
  ↓                             │
Task 6 (購物車) ←────────────────┘
  ↓
Task 7 (結帳)
  ↓
Task 8 (測試優化)
```

## Success Criteria (Technical)

### 功能驗收

✅ **人臉識別**：
- 新使用者註冊成功率 > 95%
- 回訪使用者識別成功率 > 90%
- 人臉圖片正確儲存至 `data/faces/`

✅ **商品辨識**：
- YOLO 模型成功載入
- 元翠茶、分解茶辨識準確度基於訓練模型表現
- 信心度 < 0.7 的結果自動過濾

✅ **購物車**：
- 商品自動加入、數量累加
- 移除商品功能正常
- 總價計算正確

✅ **結帳流程**：
- 交易記錄完整儲存至 MongoDB
- 包含使用者 ID、商品清單、總金額、時間戳
- 結帳後購物車正確清空

### 效能指標

- **人臉識別延遲**：< 2 秒（從偵測到顯示使用者資料）
- **商品識別延遲**：< 1 秒（從掃描到加入購物車）
- **WebSocket 延遲**：< 100ms（影格傳輸）
- **系統穩定性**：連續運行 2 小時無崩潰

### 程式碼品質

- 模組化設計，職責清晰分離
- 錯誤處理完整（鏡頭存取失敗、MongoDB 斷線）
- 關鍵函式有註解說明
- 設定檔統一管理（`config.py`）

## Estimated Effort

### 整體時程：3 週

| 階段 | 任務 | 時間 | 關鍵里程碑 |
|------|------|------|-----------|
| **Phase 1** | Task 1-3 | 5 天 | 基本架構完成，能顯示鏡頭畫面 |
| **Phase 2** | Task 4-5 | 5 天 | YOLO 和人臉識別整合完成 |
| **Phase 3** | Task 6-7 | 3 天 | 完整購物流程可用 |
| **Phase 4** | Task 8 | 2 天 | 系統優化和測試完成 |

**總工作天數**：15 天（約 3 週）

### 資源需求

- **開發人力**：1 名全端工程師
- **測試環境**：本地電腦 + 鏡頭 + MongoDB
- **選用資源**：GPU（加速 YOLO 推論）

### 關鍵路徑

```
基礎架構 → YOLO 整合 → 人臉識別 → 購物車 → 結帳 → 測試
  (5天)      (2天)      (3天)      (2天)   (1天)  (2天)
```

**優化建議**：
- Task 2 和 Task 3 可平行開發（前後端分離）
- Task 4 和 Task 5 可平行開發（AI 模組獨立）

## Simplification Opportunities

### 利用現有功能

1. **YOLO 模型**：直接使用 `runs/` 目錄中已訓練的模型，無需重新訓練
2. **資料集配置**：參考 `dataset/dataset.yaml` 獲取類別對應

### 簡化設計

1. **無需帳號系統**：人臉即為帳號，無密碼、無登入頁
2. **無需支付整合**：僅記錄交易，不處理金流
3. **無需管理後台**：直接操作 MongoDB 管理商品
4. **無狀態 Session**：購物車綁定 WebSocket 連線，斷線即清空

### 技術簡化

1. **前端無框架**：純 HTML/JS，降低學習曲線
2. **單一 WebSocket**：所有通訊走同一連線
3. **同步處理**：簡化非同步邏輯（必要時才用）
4. **本地部署**：無需考慮 HTTPS、域名、容器化

## Tasks Created

- [ ] [001.md](001.md) - 建立專案結構與 MongoDB 設定 (parallel: false, 4-6h)
- [ ] [002.md](002.md) - 實作 FastAPI 主程式與 WebSocket 通訊 (parallel: false, 4-6h, depends: 001)
- [ ] [003.md](003.md) - 建立前端頁面與鏡頭存取功能 (parallel: true, 4-6h, depends: 001)
- [ ] [004.md](004.md) - 整合 YOLO 模型並實作商品偵測服務 (parallel: true, 4-6h, depends: 001, 002)
- [ ] [005.md](005.md) - 實作人臉識別服務（註冊、比對、登入）(parallel: true, 6-8h, depends: 001, 002)
- [ ] [006.md](006.md) - 實作購物車邏輯與前端 UI (parallel: false, 3-4h, depends: 002, 003, 004, 005)
- [ ] [007.md](007.md) - 實作結帳流程與交易記錄 (parallel: false, 2-3h, depends: 006)
- [ ] [008.md](008.md) - 系統整合測試、效能優化與 Bug 修復 (parallel: false, 4-6h, depends: 001-007)

**總任務數**：8 項
**可平行任務**：3 項（003, 004, 005）
**必須循序任務**：5 項
**預估總工時**：31-43 小時

### 開發順序建議

**Week 1（Phase 1: 基礎架構）**：
- Day 1-2: Task 001（專案結構和資料庫）
- Day 2-3: Task 002（FastAPI 和 WebSocket）
- Day 2-3: Task 003（前端頁面）- 可與 002 平行

**Week 2（Phase 2: AI 整合）**：
- Day 4-5: Task 004（YOLO 整合）- 可與 005 平行
- Day 4-6: Task 005（人臉識別）- 可與 004 平行

**Week 3（Phase 3-4: 業務邏輯與測試）**：
- Day 6-7: Task 006（購物車）
- Day 7: Task 007（結帳）
- Day 8-9: Task 008（測試優化）

---

**Epic 狀態**：Backlog
**建立時間**：2025-10-30T04:03:19Z
**任務建立時間**：2025-10-30T05:02:17Z
**預計工期**：3 週（15 工作天）
**任務數量**：8 項核心任務
**預估總工時**：31-43 小時
