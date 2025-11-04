#!/usr/bin/env python3
"""
購物車功能測試腳本
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.cart_service import get_cart_service


def test_cart():
    """測試購物車功能"""
    print("=" * 60)
    print("購物車功能測試")
    print("=" * 60)

    cart_service = get_cart_service()
    session_id = "test_session_12345"

    # 測試商品
    product1 = {'id': '1', 'name': '元翠茶', 'price': 150.0}
    product2 = {'id': '2', 'name': '分解茶', 'price': 200.0}

    # 測試 1: 加入商品
    print("\n測試 1: 加入第一個商品")
    result = cart_service.add_item(session_id, product1)
    print(f"   購物車狀態: {result}")
    assert len(result['items']) == 1
    assert result['total_quantity'] == 1
    assert result['total_amount'] == 150.0
    print("   ✅ 通過")

    # 測試 2: 再次加入相同商品（數量應該累加）
    print("\n測試 2: 再次加入相同商品")
    result = cart_service.add_item(session_id, product1)
    print(f"   購物車狀態: {result}")
    assert len(result['items']) == 1
    assert result['items'][0]['quantity'] == 2
    assert result['total_quantity'] == 2
    assert result['total_amount'] == 300.0
    print("   ✅ 通過")

    # 測試 3: 加入不同商品
    print("\n測試 3: 加入不同商品")
    result = cart_service.add_item(session_id, product2)
    print(f"   購物車狀態: {result}")
    assert len(result['items']) == 2
    assert result['total_quantity'] == 3
    assert result['total_amount'] == 500.0
    print("   ✅ 通過")

    # 測試 4: 移除第一個商品
    print("\n測試 4: 移除索引 0 的商品")
    result = cart_service.remove_item(session_id, 0)
    print(f"   購物車狀態: {result}")
    assert len(result['items']) == 1
    assert result['items'][0]['name'] == '分解茶'
    assert result['total_quantity'] == 1
    assert result['total_amount'] == 200.0
    print("   ✅ 通過")

    # 測試 5: 驗證購物車
    print("\n測試 5: 驗證購物車有效性")
    is_valid = cart_service.validate_cart(session_id)
    print(f"   購物車有效: {is_valid}")
    assert is_valid == True
    print("   ✅ 通過")

    # 測試 6: 清空購物車
    print("\n測試 6: 清空購物車")
    cart_service.clear_cart(session_id)
    result = cart_service.get_cart_summary(session_id)
    print(f"   購物車狀態: {result}")
    assert len(result['items']) == 0
    assert result['total_quantity'] == 0
    assert result['total_amount'] == 0
    print("   ✅ 通過")

    # 測試 7: 驗證空購物車
    print("\n測試 7: 驗證空購物車")
    is_valid = cart_service.validate_cart(session_id)
    print(f"   購物車有效: {is_valid}")
    assert is_valid == False
    print("   ✅ 通過")

    print("\n" + "=" * 60)
    print("✅ 所有測試通過！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = test_cart()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
