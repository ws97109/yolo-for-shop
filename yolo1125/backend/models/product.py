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
    description: Optional[str] = None
    category: Optional[str] = None
    stock: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProductCreate(BaseModel):
    """新增商品請求模型"""
    name: str
    price: float
    yolo_class_id: int
    yolo_class_name: str
    image: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    stock: int = Field(default=0)
    is_active: bool = Field(default=True)


class ProductUpdate(BaseModel):
    """更新商品請求模型"""
    name: Optional[str] = None
    price: Optional[float] = None
    yolo_class_id: Optional[int] = None
    yolo_class_name: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
