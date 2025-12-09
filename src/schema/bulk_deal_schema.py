# src/schema/bulk_deal_schema.py
import sys
parent_directory = 'C:/Users/Tvari/Desktop/personal/pdf_parsing/src'
sys.path.append(parent_directory)
from pydantic import BaseModel, Field
from typing import List, Optional

class BulkDealRecord(BaseModel):
    date: Optional[str] = Field(None, description="Transaction date (string)")
    client_name: Optional[str] = Field(None)
    buy_sell: Optional[str] = Field(None)
    quantity: Optional[float] = Field(None)
    price: Optional[float] = Field(None)

class BulkDealSchema(BaseModel):
    document_type: str = "bulk_deal"
    metadata: dict = {}
    records: List[BulkDealRecord] = []
    data_quality: dict = {"score": 0.0, "errors": []}
