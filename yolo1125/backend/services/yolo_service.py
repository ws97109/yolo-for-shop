"""
YOLO 商品偵測服務
載入訓練好的 YOLOv8 模型並提供商品偵測功能
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

from backend.config import YOLO_MODEL_PATH, CONFIDENCE_THRESHOLD, BASE_DIR
from backend.database import Database


class YOLOService:
    """YOLO 商品偵測服務"""

    def __init__(self):
        self.model = None
        self.product_cache = {}  # yolo_class_id -> product_info
        self.load_model()
        self.load_products()

    def load_model(self):
        """載入 YOLO 模型"""
        try:
            model_path = YOLO_MODEL_PATH

            if not model_path.exists():
                raise FileNotFoundError(f"YOLO 模型不存在: {model_path}")

            self.model = YOLO(str(model_path))
            print(f"✅ YOLO 模型載入成功: {model_path}")

            # 顯示模型資訊
            print(f"   類別數量: {len(self.model.names)}")
            print(f"   類別名稱: {self.model.names}")

        except Exception as e:
            print(f"❌ YOLO 模型載入失敗: {e}")
            raise

    def load_products(self):
        """從資料庫載入商品資訊"""
        try:
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
            if self.product_cache:
                print(f"   商品對應: {self.product_cache}")

        except Exception as e:
            print(f"❌ 載入商品資訊失敗: {e}")
            self.product_cache = {}

    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        偵測影像中的商品

        Args:
            frame: OpenCV 影像 (BGR format)

        Returns:
            偵測結果列表，每個結果包含:
            {
                'class_id': int,
                'class_name': str,
                'confidence': float,
                'bbox': [x1, y1, x2, y2],
                'product': {id, name, price} or None
            }
        """
        if self.model is None:
            return []

        try:
            # YOLO 推論
            results = self.model(frame, verbose=False)

            detections = []

            for result in results:
                boxes = result.boxes

                for box in boxes:
                    # 取得資訊
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    # 過濾低信心度
                    if confidence < CONFIDENCE_THRESHOLD:
                        continue

                    # 取得類別名稱
                    class_name = self.model.names.get(class_id, f"class_{class_id}")

                    # 查詢商品資訊
                    product = self.product_cache.get(class_id)

                    detection = {
                        'class_id': class_id,
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'product': product
                    }

                    detections.append(detection)

            return detections

        except Exception as e:
            print(f"❌ YOLO 偵測錯誤: {e}")
            return []

    def get_product_by_class_id(self, class_id: int) -> Optional[Dict]:
        """根據 YOLO class_id 查詢商品"""
        return self.product_cache.get(class_id)


# 全域單例 - 延遲初始化以避免啟動時錯誤
_yolo_service = None


def get_yolo_service() -> YOLOService:
    """獲取 YOLO 服務單例"""
    global _yolo_service
    if _yolo_service is None:
        _yolo_service = YOLOService()
    return _yolo_service
