#!/usr/bin/env python3
"""
結帳流程測試腳本
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Database
from backend.services.cart_service import get_cart_service
from backend.services.face_service import get_face_service
from bson import ObjectId
from datetime import datetime


def test_checkout():
    """測試結帳流程"""
    print("=" * 60)
    print("結帳流程測試")
    print("=" * 60)

    db = Database.connect()
    cart_service = get_cart_service()

    # 測試 1: 建立測試使用者
    print("\n測試 1: 建立測試使用者")
    test_user = {
        "name": "測試使用者",
        "phone": "0900123456",
        "face_encoding": [0.0] * 128,
        "face_image_path": "",
        "created_at": datetime.utcnow(),
        "last_visit": datetime.utcnow()
    }

    result = db.users.insert_one(test_user)
    user_id = str(result.inserted_id)
    print(f"   ✅ 建立測試使用者: {user_id}")

    # 測試 2: 建立測試購物車
    print("\n測試 2: 建立測試購物車")
    session_id = "test_checkout_session_001"
    product1 = {'id': 'prod001', 'name': '元翠茶', 'price': 150.0}
    product2 = {'id': 'prod002', 'name': '分解茶', 'price': 200.0}

    cart_service.add_item(session_id, product1)
    cart_service.add_item(session_id, product1)  # 加入兩次
    cart_service.add_item(session_id, product2)

    cart_summary = cart_service.get_cart_summary(session_id)
    print(f"   購物車商品數: {cart_summary['total_quantity']}")
    print(f"   購物車總額: NT$ {cart_summary['total_amount']}")
    assert cart_summary['total_quantity'] == 3
    assert cart_summary['total_amount'] == 500.0
    print("   ✅ 通過")

    # 測試 3: 建立交易記錄
    print("\n測試 3: 建立交易記錄")
    transaction = {
        "user_id": ObjectId(user_id),
        "user_name": test_user['name'],
        "items": cart_summary['items'],
        "total_quantity": cart_summary['total_quantity'],
        "total_amount": cart_summary['total_amount'],
        "created_at": datetime.utcnow()
    }

    result = db.transactions.insert_one(transaction)
    transaction_id = str(result.inserted_id)
    print(f"   交易 ID: {transaction_id}")
    print("   ✅ 通過")

    # 測試 4: 驗證交易記錄
    print("\n測試 4: 驗證交易記錄")
    saved_txn = db.transactions.find_one({"_id": result.inserted_id})
    assert saved_txn is not None
    assert saved_txn['user_name'] == test_user['name']
    assert saved_txn['total_amount'] == 500.0
    assert len(saved_txn['items']) == 2  # 兩種商品
    print(f"   使用者: {saved_txn['user_name']}")
    print(f"   總金額: NT$ {saved_txn['total_amount']}")
    print(f"   商品數: {len(saved_txn['items'])}")
    print("   ✅ 通過")

    # 測試 5: 清空購物車
    print("\n測試 5: 清空購物車")
    cart_service.clear_cart(session_id)
    cart_summary = cart_service.get_cart_summary(session_id)
    assert len(cart_summary['items']) == 0
    assert cart_summary['total_amount'] == 0
    print("   ✅ 通過")

    # 測試 6: 驗證購物車無效（空）
    print("\n測試 6: 驗證空購物車")
    is_valid = cart_service.validate_cart(session_id)
    assert is_valid == False
    print("   ✅ 通過")

    # 清理測試資料
    print("\n清理測試資料...")
    db.users.delete_one({"_id": ObjectId(user_id)})
    db.transactions.delete_one({"_id": result.inserted_id})
    print("   🧹 清理完成")

    print("\n" + "=" * 60)
    print("✅ 所有測試通過！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = test_checkout()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
