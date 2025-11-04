from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class TransactionItem(BaseModel):
    """交易商品項目"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

class Transaction(BaseModel):
    """交易記錄"""
    id: Optional[str] = Field(None, alias='_id')
    user_id: str
    user_name: str
    items: List[TransactionItem]
    total_quantity: int
    total_amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }
