"""
資料庫初始化腳本
初始化 MongoDB Collections 和商品資料
"""
import sys
from pathlib import Path
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Database, init_collections

def main():
    """初始化資料庫"""
    print("="*60)
    print("開始初始化資料庫...")
    print("="*60)

    try:
        # 連接資料庫
        db = Database.connect()

        # 建立索引
        print("\n建立 Collections 索引...")
        init_collections()

        # 插入初始商品資料
        print("\n插入初始商品資料...")
        products = [
            {
                "name": "元翠茶",
                "price": 150.0,
                "yolo_class_id": 0,
                "yolo_class_name": "yuancui_tea",
                "created_at": datetime.utcnow()
            },
            {
                "name": "分解茶",
                "price": 200.0,
                "yolo_class_id": 1,
                "yolo_class_name": "fenjie_tea",
                "created_at": datetime.utcnow()
            }
        ]

        # 清空現有資料（開發階段）
        existing_count = db.products.count_documents({})
        if existing_count > 0:
            print(f"   清空現有商品資料 ({existing_count} 筆)")
            db.products.delete_many({})

        # 插入商品
        result = db.products.insert_many(products)
        print(f"✅ 插入 {len(result.inserted_ids)} 個商品")

        # 顯示商品清單
        print("\n商品清單：")
        for product in db.products.find():
            print(f"  - {product['name']}: NT$ {product['price']} (YOLO ID: {product['yolo_class_id']})")

        # 顯示統計資訊
        print("\n" + "="*60)
        print("資料庫統計：")
        print(f"  商品數量: {db.products.count_documents({})}")
        print(f"  使用者數量: {db.users.count_documents({})}")
        print(f"  交易記錄: {db.transactions.count_documents({})}")
        print("="*60)

        print("\n✅ 資料庫初始化完成！")
        print("\n下一步：執行 'python backend/main.py' 啟動系統")

    except Exception as e:
        print(f"\n❌ 初始化失敗: {e}")
        print("\n請確認：")
        print("  1. MongoDB 服務已啟動")
        print("  2. 連線設定正確 (backend/config.py)")
        sys.exit(1)

if __name__ == "__main__":
    main()
