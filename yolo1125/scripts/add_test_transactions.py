#!/usr/bin/env python3
"""
新增測試交易記錄
為現有使用者建立購買記錄，包含兩種商品：元翠茶(150元)和分解茶(200元)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
from bson import ObjectId

# MongoDB 連線設定
MONGODB_URL = "mongodb://localhost:27017"
DB_NAME = "yolo1125"

def get_db():
    """取得資料庫連線"""
    client = MongoClient(MONGODB_URL)
    return client[DB_NAME]

def get_products():
    """取得商品列表"""
    db = get_db()
    products = list(db.products.find())

    if not products:
        print("❌ 資料庫中沒有商品,請先執行 init_db.py")
        sys.exit(1)

    print(f"✅ 找到 {len(products)} 種商品:")
    for p in products:
        print(f"   - {p['name']}: ${p['price']} (ID: {p['_id']})")

    return products

def get_users():
    """取得使用者列表"""
    db = get_db()
    users = list(db.users.find())

    if not users:
        print("❌ 資料庫中沒有使用者,請先註冊使用者")
        sys.exit(1)

    print(f"\n✅ 找到 {len(users)} 位使用者:")
    for u in users:
        print(f"   - {u['name']} ({u['phone']}) - ID: {u['_id']}")

    return users

def create_transaction(user, products, days_ago=0):
    """建立單筆交易記錄"""
    db = get_db()

    # 隨機選擇商品和數量
    num_items = random.randint(1, 3)  # 購買 1-3 個商品
    items = []
    total_quantity = 0
    total_amount = 0

    for _ in range(num_items):
        product = random.choice(products)
        quantity = random.randint(1, 3)  # 每種商品買 1-3 件

        item = {
            "product_id": str(product['_id']),
            "product_name": product['name'],
            "quantity": quantity,
            "unit_price": product['price'],
            "subtotal": product['price'] * quantity
        }

        items.append(item)
        total_quantity += quantity
        total_amount += item['subtotal']

    # 計算交易時間 (往前推算 N 天)
    transaction_time = datetime.utcnow() - timedelta(days=days_ago)

    # 建立交易記錄
    transaction = {
        "user_id": user['_id'],
        "user_name": user['name'],
        "items": items,
        "total_quantity": total_quantity,
        "total_amount": total_amount,
        "created_at": transaction_time
    }

    result = db.transactions.insert_one(transaction)

    return result.inserted_id, transaction

def main():
    print("=" * 60)
    print("📦 新增測試交易記錄")
    print("=" * 60)

    # 取得商品和使用者
    products = get_products()
    users = get_users()

    print("\n" + "=" * 60)
    print("🛒 開始建立測試交易記錄")
    print("=" * 60)

    total_transactions = 0

    # 為每個使用者建立 3-5 筆交易記錄
    for user in users:
        num_transactions = random.randint(3, 5)
        print(f"\n為 {user['name']} 建立 {num_transactions} 筆交易記錄:")

        for i in range(num_transactions):
            # 交易時間分散在過去 30 天內
            days_ago = random.randint(0, 30)

            transaction_id, transaction = create_transaction(user, products, days_ago)

            # 顯示交易詳情
            items_text = ", ".join([
                f"{item['product_name']} x{item['quantity']}"
                for item in transaction['items']
            ])

            print(f"   ✅ 交易 #{i+1}: ${transaction['total_amount']:.0f} ({items_text})")
            print(f"      時間: {transaction['created_at'].strftime('%Y-%m-%d %H:%M')}")
            print(f"      ID: {transaction_id}")

            total_transactions += 1

    print("\n" + "=" * 60)
    print(f"✅ 成功建立 {total_transactions} 筆測試交易記錄")
    print("=" * 60)

    # 顯示統計
    db = get_db()

    print("\n📊 交易統計:")
    for user in users:
        user_transactions = list(db.transactions.find({"user_id": user['_id']}))
        total_spent = sum(t['total_amount'] for t in user_transactions)
        total_items = sum(t['total_quantity'] for t in user_transactions)

        print(f"\n   {user['name']}:")
        print(f"   - 交易次數: {len(user_transactions)} 次")
        print(f"   - 購買商品: {total_items} 件")
        print(f"   - 累積消費: ${total_spent:.0f}")

if __name__ == "__main__":
    main()
