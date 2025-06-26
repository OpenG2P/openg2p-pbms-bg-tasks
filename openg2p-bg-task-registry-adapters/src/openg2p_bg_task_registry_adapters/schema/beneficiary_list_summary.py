from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class GeneralSummary(BaseModel):
    id: int
    program_id: int
    program_mnemonic: str
    target_registry: str
    beneficiary_list_id: str
    number_of_registrants: Any
    date_created: Optional[datetime]
    total_entitlement_amount: Optional[dict] = None
    average_entitlement_per_registrant: Optional[dict] = None


class SummaryPayload(BaseModel):
    general_summary: GeneralSummary
