from typing import Optional
from datetime import date

from .registry import G2PRegistryPayload


class G2PFarmerRegistryDailyPayload(G2PRegistryPayload):
    unique_id: Optional[int] = None
    nrc_number: Optional[str] = None
    attendance_date: Optional[date] = None  # Use str for date, or datetime/date if you want stricter typing
    task: Optional[str] = None
