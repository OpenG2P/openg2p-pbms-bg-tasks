from datetime import datetime

from pydantic import BaseModel


class G2PRegistryResponse(BaseModel):
    id: int
    unique_id: str
    registration_date: datetime
