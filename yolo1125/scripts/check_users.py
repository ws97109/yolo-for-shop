#!/usr/bin/env python3
"""
檢查資料庫中的使用者資料
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database import Database

def main():
    """檢查使用者資料"""
    try:
        db = Database.get_db()

        users = list(db.users.find())

        print(f"\n{'=' * 60}")
        print(f"資料庫使用者列表 (共 {len(users)} 位)")
        print('=' * 60)

        if not users:
            print("⚠️  資料庫中沒有使用者資料")
        else:
            for i, user in enumerate(users, 1):
                print(f"\n使用者 {i}:")
                print(f"  ID: {user['_id']}")
                print(f"  姓名: {user.get('name', 'N/A')}")
                print(f"  電話: {user.get('phone', 'N/A')}")
                print(f"  人臉特徵: {'✅ 已儲存' if user.get('face_encoding') else '❌ 未儲存'}")
                print(f"  人臉圖片: {user.get('face_image_path', 'N/A')}")
                print(f"  註冊時間: {user.get('created_at', 'N/A')}")
                print(f"  最後訪問: {user.get('last_visit', 'N/A')}")

        print(f"\n{'=' * 60}\n")

    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    main()
