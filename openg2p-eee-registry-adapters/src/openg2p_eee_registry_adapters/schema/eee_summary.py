from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EEESummaryPayload(BaseModel):
    id: int
    program_id: int
    program_mnemonic: str
    target_registry_type: str
    pbms_request_id: str
    number_of_registrants: int
    date_created: Optional[datetime]
