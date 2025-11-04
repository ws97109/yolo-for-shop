"""
人臉識別服務
使用 face_recognition 進行人臉偵測、特徵提取、比對和註冊
"""

import face_recognition
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from bson import ObjectId

from backend.config import FACE_IMAGES_DIR, FACE_MATCH_TOLERANCE, BASE_DIR
from backend.database import Database


class FaceService:
    """人臉識別服務"""

    def __init__(self):
        self.known_faces = {}  # user_id -> face_encoding
        self.known_users = {}  # user_id -> user_info
        self.load_known_faces()

        # 確保人臉圖片目錄存在
        FACE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    def load_known_faces(self):
        """從資料庫載入已知人臉"""
        try:
            db = Database.get_db()
            users = db.users.find({})

            for user in users:
                user_id = str(user['_id'])
                face_encoding = user.get('face_encoding')

                if face_encoding:
                    self.known_faces[user_id] = np.array(face_encoding)
                    self.known_users[user_id] = {
                        'id': user_id,
                        'name': user['name'],
                        'phone': user['phone'],
                        'created_at': user.get('created_at', datetime.utcnow()).isoformat()
                    }

            print(f"✅ 載入 {len(self.known_faces)} 個已知人臉")

        except Exception as e:
            print(f"❌ 載入人臉資料失敗: {e}")
            self.known_faces = {}
            self.known_users = {}

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        偵測影像中的人臉

        Args:
            frame: OpenCV 影像 (BGR format)

        Returns:
            [(face_encoding, (top, right, bottom, left)), ...]
        """
        try:
            # 轉換為 RGB（face_recognition 需要）
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 偵測人臉位置
            face_locations = face_recognition.face_locations(rgb_frame, model='hog')

            if not face_locations:
                return []

            # 提取人臉特徵
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            results = []
            for encoding, location in zip(face_encodings, face_locations):
                results.append((encoding, location))

            return results

        except Exception as e:
            print(f"❌ 人臉偵測錯誤: {e}")
            return []

    def match_face(self, face_encoding: np.ndarray) -> Optional[Dict]:
        """
        比對人臉，找出已知使用者

        Args:
            face_encoding: 128-d 人臉特徵向量

        Returns:
            使用者資訊 {id, name, phone, distance, created_at} 或 None
        """
        if not self.known_faces:
            return None

        try:
            # 計算與所有已知人臉的距離
            known_ids = list(self.known_faces.keys())
            known_encodings = [self.known_faces[uid] for uid in known_ids]

            face_distances = face_recognition.face_distance(known_encodings, face_encoding)

            # 找出最相似的
            best_match_index = np.argmin(face_distances)
            best_distance = face_distances[best_match_index]

            # 檢查是否在容忍範圍內
            if best_distance < FACE_MATCH_TOLERANCE:
                user_id = known_ids[best_match_index]
                user_info = self.known_users[user_id].copy()
                user_info['distance'] = float(best_distance)

                # 更新最後訪問時間
                self.update_last_visit(user_id)

                return user_info

            return None

        except Exception as e:
            print(f"❌ 人臉比對錯誤: {e}")
            return None

    def register_user(self, name: str, phone: str, face_encoding: np.ndarray, face_image: np.ndarray, birthday: str = None) -> Dict:
        """
        註冊新使用者

        Args:
            name: 姓名
            phone: 電話
            face_encoding: 人臉特徵向量
            face_image: 人臉圖片 (BGR format)
            birthday: 生日 (ISO format string)

        Returns:
            使用者資訊 {id, name, phone, birthday, created_at}
        """
        try:
            db = Database.get_db()

            # 檢查電話是否已存在
            existing_user = db.users.find_one({'phone': phone})
            if existing_user:
                raise ValueError(f"電話號碼 {phone} 已被註冊")

            # 建立使用者文件
            user_doc = {
                'name': name,
                'phone': phone,
                'face_encoding': face_encoding.tolist(),
                'face_image_path': '',  # 稍後更新
                'created_at': datetime.utcnow(),
                'last_visit': datetime.utcnow()
            }

            # 添加生日（如果提供）
            if birthday:
                try:
                    # 嘗試解析日期字符串 (YYYY-MM-DD format)
                    user_doc['birthday'] = datetime.fromisoformat(birthday.replace('Z', '+00:00'))
                except:
                    # 如果解析失敗，嘗試其他格式
                    try:
                        user_doc['birthday'] = datetime.strptime(birthday, '%Y-%m-%d')
                    except:
                        # 仍然失敗，保存為字符串
                        user_doc['birthday'] = birthday

            result = db.users.insert_one(user_doc)
            user_id = str(result.inserted_id)

            # 儲存人臉圖片
            image_path = FACE_IMAGES_DIR / f"{user_id}.jpg"
            cv2.imwrite(str(image_path), face_image)

            # 更新圖片路徑
            db.users.update_one(
                {'_id': result.inserted_id},
                {'$set': {'face_image_path': str(image_path)}}
            )

            # 加入記憶體快取
            self.known_faces[user_id] = face_encoding
            self.known_users[user_id] = {
                'id': user_id,
                'name': name,
                'phone': phone,
                'created_at': user_doc['created_at'].isoformat()
            }

            print(f"✅ 使用者註冊成功: {name} ({phone})")

            result_dict = {
                'id': user_id,
                'name': name,
                'phone': phone,
                'created_at': user_doc['created_at'].isoformat()
            }

            if birthday:
                result_dict['birthday'] = birthday

            return result_dict

        except Exception as e:
            print(f"❌ 使用者註冊失敗: {e}")
            raise

    def update_last_visit(self, user_id: str):
        """更新使用者最後訪問時間"""
        try:
            db = Database.get_db()
            db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'last_visit': datetime.utcnow()}}
            )
        except Exception as e:
            print(f"⚠️ 更新最後訪問時間失敗: {e}")

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """根據 ID 取得使用者資訊"""
        try:
            db = Database.get_db()
            user = db.users.find_one({'_id': ObjectId(user_id)})

            if user:
                return {
                    'id': str(user['_id']),
                    'name': user['name'],
                    'phone': user['phone'],
                    'created_at': user['created_at'].isoformat() if user.get('created_at') else None
                }

            return None

        except Exception as e:
            print(f"❌ 取得使用者失敗: {e}")
            return None


# 全域單例 - 延遲初始化
_face_service = None


def get_face_service() -> FaceService:
    """獲取人臉服務單例"""
    global _face_service
    if _face_service is None:
        _face_service = FaceService()
    return _face_service
