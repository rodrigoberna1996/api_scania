from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class TravelLogItem(BaseModel):
    id: int
    fields: Dict[str, Any]
    created_at: datetime
    modified_at: datetime
