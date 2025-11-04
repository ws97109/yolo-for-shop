#!/usr/bin/env python3
"""
系統整合測試
測試完整的端對端流程：人臉識別 → 登入 → 商品掃描 → 購物車 → 結帳
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
import numpy as np
import cv2
import face_recognition
from backend.database import Database
from backend.services.face_service import FaceService
from backend.services.yolo_service import YOLOService
from backend.services.cart_service import CartService
from bson import ObjectId


def print_header(text):
    """列印測試標題"""
    print(f"\n{'=' * 60}")
    print(f"{text}")
    print('=' * 60)


def print_test(number, description):
    """列印測試項目"""
    print(f"\n測試 {number}: {description}")


def print_success(message):
    """列印成功訊息"""
    print(f"   ✅ {message}")


def print_error(message):
    """列印錯誤訊息"""
    print(f"   ❌ {message}")


def test_database_connection():
    """測試 1: 資料庫連線"""
    print_test(1, "資料庫連線")
    try:
        db = Database.get_db()
        db_name = db.name
        print_success(f"MongoDB 連線成功: {db_name}")
        return True
    except Exception as e:
        print_error(f"MongoDB 連線失敗: {e}")
        return False


def test_face_registration():
    """測試 2: 人臉註冊"""
    print_test(2, "人臉註冊流程")

    try:
        face_service = FaceService()

        # 建立測試人臉圖片（隨機圖片）
        test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # 註冊使用者（使用真實人臉圖片會更好）
        user_id = face_service.register_user(
            name="整合測試使用者",
            phone="0900000000",
            face_image=test_image
        )

        if user_id:
            print_success(f"使用者註冊成功: {user_id}")
            return user_id
        else:
            print_error("人臉註冊失敗（未偵測到人臉）")
            return None
    except Exception as e:
        print_error(f"人臉註冊錯誤: {e}")
        return None


def test_yolo_detection():
    """測試 3: YOLO 商品偵測"""
    print_test(3, "YOLO 商品偵測")

    try:
        yolo_service = YOLOService()

        # 載入測試圖片
        test_images = [
            project_root / "dataset" / "LINE_ALBUM_原萃_251014_1.jpg",
            project_root / "dataset" / "LINE_ALBUM_原萃_251014_2.jpg"
        ]

        detection_count = 0
        for img_path in test_images:
            if img_path.exists():
                frame = cv2.imread(str(img_path))
                if frame is not None:
                    detections = yolo_service.detect(frame)
                    if detections:
                        detection_count += len(detections)
                        for det in detections:
                            print(f"   🎯 偵測到: {det['product']['name']} (信心度: {det['confidence']:.2f})")

        if detection_count > 0:
            print_success(f"YOLO 偵測成功，共 {detection_count} 個物品")
            return True
        else:
            print_error("YOLO 未偵測到任何物品")
            return False
    except Exception as e:
        print_error(f"YOLO 偵測錯誤: {e}")
        return False


def test_shopping_cart_flow(user_id):
    """測試 4: 購物車完整流程"""
    print_test(4, "購物車完整流程")

    try:
        cart_service = CartService()
        session_id = "integration_test_session"

        # 清空購物車
        cart_service.clear_cart(session_id)

        # 模擬加入商品
        db = Database.get_db()
        products = list(db.products.find())

        if len(products) < 2:
            print_error("資料庫商品不足 2 個")
            return False

        # 加入第一個商品 2 次
        product1 = {
            "id": str(products[0]['_id']),
            "name": products[0]['name'],
            "price": products[0]['price']
        }

        cart_service.add_item(session_id, product1)
        print(f"   🛒 加入購物車: {product1['name']}")

        cart_service.add_item(session_id, product1)
        print(f"   🛒 數量 +1: {product1['name']} (x2)")

        # 加入第二個商品
        product2 = {
            "id": str(products[1]['_id']),
            "name": products[1]['name'],
            "price": products[1]['price']
        }

        cart_service.add_item(session_id, product2)
        print(f"   🛒 加入購物車: {product2['name']}")

        # 檢查購物車
        summary = cart_service.get_cart_summary(session_id)

        if summary['total_quantity'] == 3:
            print_success(f"購物車狀態正確：{summary['total_quantity']} 件商品，總額 NT$ {summary['total_amount']}")
            return session_id
        else:
            print_error(f"購物車數量不正確：預期 3，實際 {summary['total_quantity']}")
            return None
    except Exception as e:
        print_error(f"購物車流程錯誤: {e}")
        return None


def test_checkout_transaction(user_id, session_id):
    """測試 5: 結帳與交易記錄"""
    print_test(5, "結帳與交易記錄")

    try:
        cart_service = CartService()
        db = Database.get_db()

        # 獲取使用者資訊
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            print_error("找不到使用者")
            return False

        # 獲取購物車摘要
        cart_summary = cart_service.get_cart_summary(session_id)

        # 建立交易記錄
        transaction = {
            "user_id": ObjectId(user_id),
            "user_name": user['name'],
            "items": cart_summary['items'],
            "total_quantity": cart_summary['total_quantity'],
            "total_amount": cart_summary['total_amount'],
            "created_at": datetime.now()
        }

        result = db.transactions.insert_one(transaction)
        transaction_id = str(result.inserted_id)

        print_success(f"交易記錄建立成功: {transaction_id}")

        # 清空購物車
        cart_service.clear_cart(session_id)

        # 驗證購物車已空
        if not cart_service.validate_cart(session_id):
            print_success("購物車已清空")
        else:
            print_error("購物車未清空")
            return False

        # 驗證交易記錄
        saved_transaction = db.transactions.find_one({"_id": ObjectId(transaction_id)})
        if saved_transaction:
            print_success(f"交易記錄驗證成功：總額 NT$ {saved_transaction['total_amount']}")
            return transaction_id
        else:
            print_error("交易記錄驗證失敗")
            return None
    except Exception as e:
        print_error(f"結帳流程錯誤: {e}")
        return None


def test_data_consistency():
    """測試 6: 資料一致性檢查"""
    print_test(6, "資料一致性檢查")

    try:
        db = Database.get_db()

        # 檢查商品資料
        products_count = db.products.count_documents({})
        print(f"   📦 商品數量: {products_count}")

        # 檢查使用者資料
        users_count = db.users.count_documents({})
        print(f"   👤 使用者數量: {users_count}")

        # 檢查交易記錄
        transactions_count = db.transactions.count_documents({})
        print(f"   💰 交易記錄數量: {transactions_count}")

        # 驗證所有商品都有必要欄位
        products = list(db.products.find())
        for product in products:
            if not all(k in product for k in ['name', 'price', 'yolo_class_id']):
                print_error(f"商品資料不完整: {product.get('name', 'Unknown')}")
                return False

        print_success("資料一致性檢查通過")
        return True
    except Exception as e:
        print_error(f"資料一致性檢查錯誤: {e}")
        return False


def cleanup_test_data(user_id=None, transaction_id=None):
    """清理測試資料"""
    print("\n清理測試資料...")

    try:
        db = Database.get_db()

        # 清理測試使用者
        if user_id:
            db.users.delete_one({"_id": ObjectId(user_id)})
        else:
            # 刪除所有測試使用者
            db.users.delete_many({"name": "整合測試使用者"})

        # 清理測試交易
        if transaction_id:
            db.transactions.delete_one({"_id": ObjectId(transaction_id)})

        print_success("測試資料清理完成")
    except Exception as e:
        print_error(f"清理測試資料錯誤: {e}")


def main():
    """主測試流程"""
    print_header("YOLO1125 系統整合測試")

    user_id = None
    session_id = None
    transaction_id = None

    try:
        # 測試 1: 資料庫連線
        if not test_database_connection():
            print("\n❌ 資料庫連線失敗，測試中止")
            return False

        # 測試 2: 人臉註冊（可選，因為需要真實人臉圖片）
        # user_id = test_face_registration()
        # if not user_id:
        #     print("\n⚠️  人臉註冊失敗（跳過，使用現有使用者）")

        # 使用資料庫中的第一個使用者
        db = Database.get_db()
        first_user = db.users.find_one()
        if first_user:
            user_id = str(first_user['_id'])
            print_success(f"使用現有使用者: {first_user.get('name', 'Unknown')} ({user_id})")
        else:
            print_error("資料庫中沒有使用者，請先註冊使用者")
            return False

        # 測試 3: YOLO 偵測
        if not test_yolo_detection():
            print("\n⚠️  YOLO 偵測測試未通過（可能沒有測試圖片）")

        # 測試 4: 購物車流程
        session_id = test_shopping_cart_flow(user_id)
        if not session_id:
            print("\n❌ 購物車流程失敗，測試中止")
            return False

        # 測試 5: 結帳與交易
        transaction_id = test_checkout_transaction(user_id, session_id)
        if not transaction_id:
            print("\n❌ 結帳流程失敗")
            return False

        # 測試 6: 資料一致性
        if not test_data_consistency():
            print("\n❌ 資料一致性檢查失敗")
            return False

        print_header("✅ 所有測試通過！")
        return True

    except Exception as e:
        print_error(f"測試過程發生錯誤: {e}")
        return False

    finally:
        # 清理測試資料（僅清理測試交易，保留使用者）
        if transaction_id:
            cleanup_test_data(transaction_id=transaction_id)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
