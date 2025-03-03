from datetime import datetime
from typing import Optional

from .registry import G2PRegistry


class G2PStudentRegistry(G2PRegistry):
    name: str
    institution_name: Optional[str]
    date_of_birth: Optional[datetime]
