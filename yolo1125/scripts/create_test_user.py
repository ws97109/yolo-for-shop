#!/usr/bin/env python3
"""
建立測試使用者
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
import numpy as np
from backend.database import Database
from bson import ObjectId

def main():
    """建立測試使用者"""
    try:
        db = Database.get_db()

        # 檢查是否已有測試使用者
        existing_user = db.users.find_one({"phone": "0912345678"})
        if existing_user:
            print(f"✅ 測試使用者已存在: {existing_user['name']} ({existing_user['_id']})")
            return str(existing_user['_id'])

        # 建立測試使用者（不含人臉編碼）
        user = {
            "name": "測試使用者",
            "phone": "0912345678",
            "face_encoding": [0.0] * 128,  # 假的人臉編碼
            "created_at": datetime.now(),
            "last_visit": datetime.now()
        }

        result = db.users.insert_one(user)
        user_id = str(result.inserted_id)

        print(f"✅ 測試使用者建立成功: {user['name']} ({user_id})")
        return user_id

    except Exception as e:
        print(f"❌ 建立測試使用者失敗: {e}")
        return None

if __name__ == "__main__":
    main()
