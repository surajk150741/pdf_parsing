# src/schema/shareholding_schema.py
import sys
parent_directory = 'C:/Users/Tvari/Desktop/personal/pdf_parsing/src'
sys.path.append(parent_directory)
from pydantic import BaseModel, Field
from typing import List, Optional

class ShareholderRecord(BaseModel):
    category: Optional[str] = None
    num_shares: Optional[float] = None
    percentage: Optional[float] = None

class ShareholdingSchema(BaseModel):
    document_type: str = "shareholding_pattern"
    metadata: dict = Field(default_factory=dict)  # company_name, quarter, source_url
    shareholders: List[ShareholderRecord] = []
    data_quality: dict = {"score": 0.0, "errors": []}
