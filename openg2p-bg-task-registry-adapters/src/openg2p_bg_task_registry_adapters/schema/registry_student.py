from datetime import datetime
from typing import Optional

from .registry import G2PRegistryPayload


class G2PStudentRegistryPayload(G2PRegistryPayload):
    name: str
    gender: Optional[str] = None
    institution_name: Optional[str]
    date_of_birth: Optional[datetime]
    small_area_code: Optional[str] = None
    large_area_code: Optional[str] = None
