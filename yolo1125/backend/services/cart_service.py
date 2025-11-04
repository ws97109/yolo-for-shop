"""
購物車服務
管理每個 session 的購物車狀態
"""

from typing import List, Dict, Optional
from datetime import datetime


class CartService:
    """購物車服務"""

    def __init__(self):
        # 使用 session_id 管理每個連線的購物車
        self.carts: Dict[str, List[Dict]] = {}

    def get_cart(self, session_id: str) -> List[Dict]:
        """取得購物車"""
        if session_id not in self.carts:
            self.carts[session_id] = []
        return self.carts[session_id]

    def add_item(self, session_id: str, product: Dict) -> Dict:
        """
        加入商品到購物車

        Args:
            session_id: Session ID
            product: 商品資訊 {id, name, price, ...}

        Returns:
            更新後的購物車狀態
        """
        cart = self.get_cart(session_id)
        product_id = product['id']

        # 檢查商品是否已存在
        existing_item = None
        for item in cart:
            if item['product_id'] == product_id:
                existing_item = item
                break

        if existing_item:
            # 商品已存在，數量 +1
            existing_item['quantity'] += 1
            existing_item['subtotal'] = existing_item['quantity'] * existing_item['unit_price']
            print(f"🛒 商品數量 +1: {existing_item['name']} (x{existing_item['quantity']})")
        else:
            # 新商品
            new_item = {
                'product_id': product_id,
                'name': product['name'],
                'unit_price': product['price'],
                'quantity': 1,
                'subtotal': product['price']
            }
            cart.append(new_item)
            print(f"🛒 加入購物車: {new_item['name']}")

        return self.get_cart_summary(session_id)

    def remove_item(self, session_id: str, index: int) -> Dict:
        """
        移除購物車中的商品

        Args:
            session_id: Session ID
            index: 商品索引

        Returns:
            更新後的購物車狀態
        """
        cart = self.get_cart(session_id)

        if 0 <= index < len(cart):
            removed_item = cart.pop(index)
            print(f"🗑️  移除商品: {removed_item['name']}")
        else:
            print(f"⚠️  無效的商品索引: {index}")

        return self.get_cart_summary(session_id)

    def clear_cart(self, session_id: str):
        """清空購物車"""
        if session_id in self.carts:
            del self.carts[session_id]
            print(f"🧹 購物車已清空: {session_id}")

    def get_cart_summary(self, session_id: str) -> Dict:
        """
        取得購物車摘要

        Returns:
            {
                'items': [...],
                'total_quantity': int,
                'total_amount': float
            }
        """
        cart = self.get_cart(session_id)

        total_quantity = sum(item['quantity'] for item in cart)
        total_amount = sum(item['subtotal'] for item in cart)

        return {
            'items': cart,
            'total_quantity': total_quantity,
            'total_amount': total_amount
        }

    def validate_cart(self, session_id: str) -> bool:
        """驗證購物車是否有效（至少一件商品）"""
        cart = self.get_cart(session_id)
        return len(cart) > 0


# 全域單例
_cart_service = None


def get_cart_service() -> CartService:
    """獲取購物車服務單例"""
    global _cart_service
    if _cart_service is None:
        _cart_service = CartService()
    return _cart_service
