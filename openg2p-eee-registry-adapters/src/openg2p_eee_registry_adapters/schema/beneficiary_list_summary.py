from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class EEEGeneralSummary(BaseModel):
    id: int
    program_id: int
    program_mnemonic: str
    target_registry_type: str
    beneficiary_list_id: str
    number_of_registrants: Any
    date_created: Optional[datetime]
    total_entitlement_amount: Optional[dict] = None
    average_entitlement_per_registrant: Optional[dict] = None


class EEESummaryPayload(BaseModel):
    general_summary: EEEGeneralSummary
