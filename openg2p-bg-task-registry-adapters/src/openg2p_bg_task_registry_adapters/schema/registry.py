from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class G2PRegistryPayload(BaseModel):
    id: int
    unique_id: str
    registration_date: Optional[datetime]
