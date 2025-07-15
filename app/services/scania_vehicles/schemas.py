from pydantic import BaseModel
from typing import Dict

class VehicleMapResponse(BaseModel):
    economic_to_vin: Dict[str, str]
