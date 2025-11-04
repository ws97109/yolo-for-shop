# YOLO1125 智慧無人商店系統

結合 YOLO 物品辨識與人臉識別的智慧結帳系統。

## 功能特色

- 🎯 **YOLO 商品識別**：自動辨識元翠茶、分解茶
- 👤 **人臉識別登入**：自動識別回訪使用者
- 🛒 **即時購物車**：商品自動加入、數量累加
- 💰 **自動結帳**：完整交易記錄儲存
- 📱 **響應式介面**：支援桌面和平板

## 系統需求

### 硬體
- 電腦（8GB+ RAM 建議）
- 網路攝影機
- （選用）NVIDIA GPU（加速 YOLO 推論）

### 軟體
- Python 3.8+
- MongoDB 6.0+
- 現代瀏覽器（Chrome, Edge, Firefox）

## 安裝步驟

### 1. 安裝 MongoDB

**macOS (Homebrew)**:
```bash
brew tap mongodb/brew
brew install mongodb-community@6.0
brew services start mongodb-community@6.0
```

**Ubuntu**:
```bash
sudo apt-get install -y mongodb
sudo systemctl start mongodb
```

**驗證 MongoDB 運行**:
```bash
mongosh
# 應該可以成功連線
```

### 2. 進入專案目錄

```bash
cd yolo1125
```

### 3. 安裝 Python 依賴

```bash
pip install -r requirements.txt
```

**注意**：
- `dlib` 需要 CMake，如未安裝請先安裝：
  - macOS: `brew install cmake`
  - Ubuntu: `sudo apt-get install cmake`

### 4. 初始化資料庫

```bash
python scripts/init_db.py
```

應該會看到：
```
✅ MongoDB 連線成功
✅ 插入 2 個商品
✅ 資料庫初始化完成！
```

## 啟動系統

**重要**：請確保先切換到 `yolo1125/` 目錄

```bash
# 從 yolo 目錄切換到 yolo1125
cd yolo1125

# 啟動後端伺服器
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

開啟瀏覽器訪問：`http://localhost:8000`

## 使用流程

### 1. 首次使用（註冊）
1. 站在鏡頭前
2. 系統偵測到人臉
3. 輸入姓名和電話註冊
4. 系統儲存人臉資料
5. 自動登入並開始購物

### 2. 回訪使用（自動登入）
1. 站在鏡頭前
2. 系統自動識別人臉
3. 顯示「歡迎回來，XXX」
4. 直接開始購物

### 3. 購物
1. 展示商品（元翠茶或分解茶）給鏡頭
2. 系統自動識別並加入購物車
3. 畫面顯示綠色偵測框和商品名稱
4. 右側購物車即時更新
5. 可點擊「移除」按鈕刪除商品

### 4. 結帳
1. 確認購物車商品無誤
2. 點擊「完成結帳」按鈕
3. 確認總金額
4. 完成交易

## 專案結構

```
yolo1125/
├── backend/              # 後端程式
│   ├── main.py           # FastAPI 主程式（待建立）
│   ├── config.py         # 設定檔
│   ├── database.py       # MongoDB 連線
│   ├── models/           # 資料模型
│   │   ├── user.py
│   │   ├── product.py
│   │   └── transaction.py
│   └── services/         # 業務邏輯（待建立）
│       ├── face_service.py
│       ├── yolo_service.py
│       └── cart_service.py
├── frontend/             # 前端頁面（待建立）
│   ├── index.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── camera.js
│           ├── websocket.js
│           └── cart.js
├── data/                 # 資料目錄
│   └── faces/            # 人臉圖片
├── scripts/              # 工具腳本
│   └── init_db.py        # 資料庫初始化
├── requirements.txt      # Python 依賴
└── README.md             # 本檔案
```

## 故障排除

### MongoDB 連線失敗

```bash
# 檢查 MongoDB 狀態
brew services list | grep mongodb  # macOS
sudo systemctl status mongodb      # Linux

# 重新啟動服務
brew services restart mongodb-community@6.0  # macOS
sudo systemctl restart mongodb               # Linux

# 測試連線
mongosh
```

### 鏡頭無法啟動
- 檢查瀏覽器權限設定
- 確認鏡頭未被其他程式佔用
- 嘗試使用 Chrome 瀏覽器

### YOLO 模型未找到
- 確認 `../runs/detect/train/weights/best.pt` 存在
- 檢查 `backend/config.py` 中的 `YOLO_MODEL_PATH` 設定

### Python 套件安裝失敗

**face-recognition / dlib 安裝失敗**：
```bash
# macOS
brew install cmake
pip install dlib
pip install face-recognition

# Ubuntu
sudo apt-get install cmake
sudo apt-get install python3-dev
pip install dlib
pip install face-recognition
```

## 開發狀態

✅ Task 001: 專案結構與 MongoDB 設定 - **已完成**
✅ Task 002: FastAPI 主程式與 WebSocket - **已完成**
✅ Task 003: 前端頁面與鏡頭存取 - **已完成**
✅ Task 004: YOLO 模型整合 - **已完成**
✅ Task 005: 人臉識別服務 - **已完成**
✅ Task 006: 購物車功能 - **已完成**
✅ Task 007: 結帳流程 - **已完成**
✅ Task 008: 系統測試與優化 - **已完成**

🎉 **系統已完成開發並通過所有測試！**

## 測試報告

系統已通過以下測試：
- ✅ 資料庫連線測試
- ✅ YOLO 商品偵測測試
- ✅ 購物車完整流程測試
- ✅ 結帳與交易記錄測試
- ✅ 資料一致性檢查

詳細測試報告請參閱：
- [TEST_REPORT.md](TEST_REPORT.md) - 單元測試報告
- [TASK004_COMPLETE.md](TASK004_COMPLETE.md) - YOLO 模型整合
- [TASK005_COMPLETE.md](TASK005_COMPLETE.md) - 人臉識別服務
- [TASK007_COMPLETE.md](TASK007_COMPLETE.md) - 結帳流程

## 授權

MIT License

## 開發團隊

YOLO1125 Development Team
