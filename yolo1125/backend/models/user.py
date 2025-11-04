from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    """使用者資料模型"""
    id: Optional[str] = Field(None, alias='_id')
    name: str
    phone: str
    face_encoding: List[float]  # 128-d 人臉特徵向量
    face_image_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_visit: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
