"""
商品管理服務
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from backend.database import Database
from backend.config import BASE_DIR
import base64
import os
from pathlib import Path


class ProductService:
    """商品管理服務類別"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.products_image_dir = BASE_DIR / "data" / "products"
        self.products_image_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ ProductService 初始化完成")

    def _get_collection(self):
        """取得 products collection"""
        return Database.get_db().products

    def _format_product(self, product: dict) -> dict:
        """格式化商品資料"""
        if not product:
            return None

        product_id = str(product['_id'])

        # 處理圖片
        image_data = None
        if product.get('image'):
            # 如果是檔案路徑，讀取並轉換為 base64
            if not product['image'].startswith('data:'):
                image_path = self.products_image_dir / f"{product_id}.jpg"
                if image_path.exists():
                    try:
                        with open(image_path, 'rb') as f:
                            image_data = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
                    except Exception as e:
                        print(f"⚠️ 讀取商品圖片失敗: {e}")
            else:
                image_data = product['image']

        return {
            "id": product_id,
            "name": product.get('name', ''),
            "price": product.get('price', 0),
            "yolo_class_id": product.get('yolo_class_id'),
            "yolo_class_name": product.get('yolo_class_name', ''),
            "image": image_data,
            "description": product.get('description', ''),
            "category": product.get('category', ''),
            "stock": product.get('stock', 0),
            "is_active": product.get('is_active', True),
            "created_at": product.get('created_at').isoformat() if product.get('created_at') else None,
            "updated_at": product.get('updated_at').isoformat() if product.get('updated_at') else None
        }

    def get_all_products(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        取得所有商品（含分頁和篩選）

        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁數量
            category: 商品分類篩選
            is_active: 上架狀態篩選
            search: 搜尋關鍵字（商品名稱）

        Returns:
            包含商品列表和分頁資訊的字典
        """
        collection = self._get_collection()

        # 建立查詢條件
        query = {}
        if category:
            query['category'] = category
        if is_active is not None:
            query['is_active'] = is_active
        if search:
            query['name'] = {'$regex': search, '$options': 'i'}

        # 計算總數
        total = collection.count_documents(query)

        # 分頁查詢
        skip = (page - 1) * page_size
        products_cursor = collection.find(query).sort('created_at', -1).skip(skip).limit(page_size)

        products = [self._format_product(p) for p in products_cursor]

        return {
            "products": products,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }

    def get_product_by_id(self, product_id: str) -> Optional[dict]:
        """
        根據 ID 取得商品

        Args:
            product_id: 商品 ID

        Returns:
            商品資料或 None
        """
        try:
            collection = self._get_collection()
            product = collection.find_one({"_id": ObjectId(product_id)})
            return self._format_product(product)
        except Exception as e:
            print(f"❌ 取得商品失敗: {e}")
            return None

    def get_product_by_yolo_class(self, yolo_class_id: int) -> Optional[dict]:
        """
        根據 YOLO 類別 ID 取得商品

        Args:
            yolo_class_id: YOLO 類別 ID

        Returns:
            商品資料或 None
        """
        collection = self._get_collection()
        product = collection.find_one({"yolo_class_id": yolo_class_id})
        return self._format_product(product)

    def create_product(self, product_data: dict) -> dict:
        """
        新增商品

        Args:
            product_data: 商品資料

        Returns:
            新增的商品資料

        Raises:
            ValueError: 如果 yolo_class_id 已存在
        """
        collection = self._get_collection()

        # 檢查 yolo_class_id 是否已存在
        existing = collection.find_one({"yolo_class_id": product_data.get('yolo_class_id')})
        if existing:
            raise ValueError(f"YOLO 類別 ID {product_data.get('yolo_class_id')} 已存在")

        # 準備商品資料
        now = datetime.utcnow()
        new_product = {
            "name": product_data.get('name'),
            "price": product_data.get('price'),
            "yolo_class_id": product_data.get('yolo_class_id'),
            "yolo_class_name": product_data.get('yolo_class_name'),
            "description": product_data.get('description', ''),
            "category": product_data.get('category', ''),
            "stock": product_data.get('stock', 0),
            "is_active": product_data.get('is_active', True),
            "image": None,
            "created_at": now,
            "updated_at": now
        }

        # 插入資料庫
        result = collection.insert_one(new_product)
        product_id = str(result.inserted_id)

        # 如果有圖片，儲存圖片
        if product_data.get('image'):
            self._save_product_image(product_id, product_data['image'])
            collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"image": f"{product_id}.jpg"}}
            )

        # 重新整理 YOLO 服務的商品快取
        self._refresh_yolo_cache()

        print(f"✅ 商品新增成功: {new_product['name']} (ID: {product_id})")

        return self.get_product_by_id(product_id)

    def update_product(self, product_id: str, update_data: dict) -> Optional[dict]:
        """
        更新商品

        Args:
            product_id: 商品 ID
            update_data: 更新資料

        Returns:
            更新後的商品資料或 None

        Raises:
            ValueError: 如果商品不存在或 yolo_class_id 衝突
        """
        collection = self._get_collection()

        # 檢查商品是否存在
        existing = collection.find_one({"_id": ObjectId(product_id)})
        if not existing:
            raise ValueError("商品不存在")

        # 如果更新 yolo_class_id，檢查是否衝突
        if update_data.get('yolo_class_id') is not None:
            conflict = collection.find_one({
                "yolo_class_id": update_data['yolo_class_id'],
                "_id": {"$ne": ObjectId(product_id)}
            })
            if conflict:
                raise ValueError(f"YOLO 類別 ID {update_data['yolo_class_id']} 已被其他商品使用")

        # 準備更新資料
        update_fields = {}
        allowed_fields = ['name', 'price', 'yolo_class_id', 'yolo_class_name',
                          'description', 'category', 'stock', 'is_active']

        for field in allowed_fields:
            if field in update_data and update_data[field] is not None:
                update_fields[field] = update_data[field]

        update_fields['updated_at'] = datetime.utcnow()

        # 更新資料庫
        collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_fields}
        )

        # 如果有圖片更新，儲存圖片
        if update_data.get('image'):
            self._save_product_image(product_id, update_data['image'])
            collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"image": f"{product_id}.jpg"}}
            )

        # 重新整理 YOLO 服務的商品快取
        self._refresh_yolo_cache()

        print(f"✅ 商品更新成功: {product_id}")

        return self.get_product_by_id(product_id)

    def delete_product(self, product_id: str) -> bool:
        """
        刪除商品

        Args:
            product_id: 商品 ID

        Returns:
            是否刪除成功

        Raises:
            ValueError: 如果商品不存在
        """
        collection = self._get_collection()

        # 檢查商品是否存在
        existing = collection.find_one({"_id": ObjectId(product_id)})
        if not existing:
            raise ValueError("商品不存在")

        # 刪除商品圖片
        image_path = self.products_image_dir / f"{product_id}.jpg"
        if image_path.exists():
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"⚠️ 刪除商品圖片失敗: {e}")

        # 刪除資料庫記錄
        result = collection.delete_one({"_id": ObjectId(product_id)})

        # 重新整理 YOLO 服務的商品快取
        self._refresh_yolo_cache()

        print(f"✅ 商品刪除成功: {existing.get('name')} (ID: {product_id})")

        return result.deleted_count > 0

    def _save_product_image(self, product_id: str, image_data: str) -> str:
        """
        儲存商品圖片

        Args:
            product_id: 商品 ID
            image_data: Base64 編碼的圖片資料

        Returns:
            圖片檔案路徑
        """
        try:
            # 移除 data:image/xxx;base64, 前綴
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            # 解碼並儲存
            image_bytes = base64.b64decode(image_data)
            image_path = self.products_image_dir / f"{product_id}.jpg"

            with open(image_path, 'wb') as f:
                f.write(image_bytes)

            return str(image_path)
        except Exception as e:
            print(f"❌ 儲存商品圖片失敗: {e}")
            raise

    def _refresh_yolo_cache(self):
        """重新整理 YOLO 服務的商品快取"""
        try:
            from backend.services.yolo_service import get_yolo_service
            yolo_service = get_yolo_service()
            yolo_service.refresh_products_cache()
        except Exception as e:
            print(f"⚠️ 重新整理 YOLO 快取失敗: {e}")

    def get_categories(self) -> List[str]:
        """取得所有商品分類"""
        collection = self._get_collection()
        categories = collection.distinct('category')
        return [c for c in categories if c]

    def get_yolo_classes(self) -> List[dict]:
        """取得所有已使用的 YOLO 類別"""
        collection = self._get_collection()
        products = collection.find({}, {"yolo_class_id": 1, "yolo_class_name": 1})
        return [
            {"id": p['yolo_class_id'], "name": p.get('yolo_class_name', '')}
            for p in products
        ]


# 單例模式
_product_service = None

def get_product_service() -> ProductService:
    """取得 ProductService 單例"""
    global _product_service
    if _product_service is None:
        _product_service = ProductService()
    return _product_service
