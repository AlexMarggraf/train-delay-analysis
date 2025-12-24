from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class GermanPrecMask(BaseModel):
    station_id: int
    station_timestamp: datetime

    qn_8: Optional[int] = None
    precipitation_mm: Optional[float] = None
    precipitation_t_or_f: Optional[bool] = None
    precipitation_type: Optional[int] = None
    eor: Optional[str] = None
