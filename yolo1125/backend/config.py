import os
from pathlib import Path

# 專案根目錄
BASE_DIR = Path(__file__).parent.parent

# MongoDB 設定
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "yolo1125"

# YOLO 模型設定
YOLO_MODEL_PATH = BASE_DIR.parent / "runs" / "detect" / "supermarket_product_detector" / "weights" / "best.pt"
CONFIDENCE_THRESHOLD = 0.85

# 人臉圖片儲存
FACE_IMAGES_DIR = BASE_DIR / "data" / "faces"

# 人臉識別設定
FACE_MATCH_TOLERANCE = 0.6  # 越小越嚴格 (0.0-1.0)

# WebSocket 設定
WS_FRAME_RATE = 5  # 每秒處理 5 影格

# 管理者帳號設定
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
