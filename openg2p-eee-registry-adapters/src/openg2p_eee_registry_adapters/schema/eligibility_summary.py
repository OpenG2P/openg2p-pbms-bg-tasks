from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EligibilitySummaryResponse(BaseModel):
    id: int
    program_id: int
    program_mnemonic: str
    target_registry_type: str
    eligibility_request_id: int
    number_of_registrants: int
    date_created: Optional[datetime]
