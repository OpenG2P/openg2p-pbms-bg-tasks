from datetime import datetime, timezone
from typing import Optional

from .registry import G2PRegistryPayload


class G2PStudentRegistryPayload(G2PRegistryPayload):
    name: str
    institution_name: Optional[str]
    date_of_birth: Optional[datetime]
