from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Product(BaseModel):
    """商品資料模型"""
    id: Optional[str] = Field(None, alias='_id')
    name: str
    price: float
    yolo_class_id: int
    yolo_class_name: str
    image: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
