from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class VehicleHistoricalData(BaseModel):
    vin: str
    timestamp: datetime
    km_recorridos: float
    consumo_lts_diesel: Optional[float] = None
    lts_adblue_consumidos: Optional[float] = None

class VehicleSummaryData(BaseModel):
    vin: str
    start_timestamp: datetime
    end_timestamp: datetime
    km_recorridos: float
    consumo_lts_diesel: float
    lts_adblue_consumidos: float
    odometro: float

class VehicleHistoryResponse(BaseModel):
    historical_data: List[VehicleHistoricalData]
    summary: Optional[VehicleSummaryData]
