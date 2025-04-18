from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EEEGeneralSummary(BaseModel):
    id: int
    program_id: int
    program_mnemonic: str
    target_registry_type: str
    pbms_request_id: str
    number_of_registrants: int
    date_created: Optional[datetime]
    total_entitlement_amount: Optional[float] = None
    average_entitlement_per_registrant: Optional[float] = None


class EEESummaryPayload(BaseModel):
    general_summary: EEEGeneralSummary
