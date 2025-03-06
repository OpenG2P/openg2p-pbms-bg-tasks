from datetime import datetime
from typing import Optional

from .registry import G2PRegistryResponse


class G2PStudentRegistryResponse(G2PRegistryResponse):
    name: str
    institution_name: Optional[str]
    date_of_birth: Optional[datetime]
