from dateutil import parser
from typing import Optional
import datetime

def parse_fecha(fecha_str: Optional[str]) -> Optional[datetime.datetime]:
    if not fecha_str:
        return None
    try:
        return parser.parse(fecha_str, dayfirst=True)
    except (ValueError, TypeError):
        return None
