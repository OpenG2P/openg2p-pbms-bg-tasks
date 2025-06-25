from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class G2PRegistryPayload(BaseModel):
    id: int
    unique_id: str
    bridge_disbursement_id: str
    bridge_disbursement_timestamp: datetime
    registration_date: Optional[datetime]
