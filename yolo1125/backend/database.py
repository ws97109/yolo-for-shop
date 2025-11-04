from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
from backend.config import MONGODB_URL, DB_NAME

class Database:
    """MongoDB 資料庫管理類別"""
    client = None
    db = None

    @classmethod
    def connect(cls):
        """連接 MongoDB"""
        try:
            cls.client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            # 測試連線
            cls.client.admin.command('ping')
            cls.db = cls.client[DB_NAME]
            print(f"✅ MongoDB 連線成功: {DB_NAME}")
            return cls.db
        except ConnectionFailure as e:
            print(f"❌ MongoDB 連線失敗: {e}")
            print(f"   請確認 MongoDB 服務已啟動")
            raise

    @classmethod
    def get_db(cls):
        """取得資料庫連線"""
        if cls.db is None:
            cls.connect()
        return cls.db

    @classmethod
    def close(cls):
        """關閉連線"""
        if cls.client:
            cls.client.close()
            print("MongoDB 連線已關閉")

def init_collections():
    """初始化 Collections 和索引"""
    db = Database.get_db()

    # Users Collection - 索引
    db.users.create_index([("phone", ASCENDING)], unique=True)
    print("✅ Users Collection 索引建立完成")

    # Products Collection - 索引
    db.products.create_index([("yolo_class_id", ASCENDING)], unique=True)
    print("✅ Products Collection 索引建立完成")

    # Transactions Collection - 索引
    db.transactions.create_index([("user_id", ASCENDING)])
    db.transactions.create_index([("created_at", ASCENDING)])
    print("✅ Transactions Collection 索引建立完成")
