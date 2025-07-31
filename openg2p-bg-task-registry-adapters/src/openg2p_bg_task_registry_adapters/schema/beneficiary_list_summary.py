from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class BeneficiaryListSummary(BaseModel):
    id: str
    program_id: int
    program_mnemonic: str
    target_registry: str
    beneficiary_list_id: str
    number_of_registrants: int
    date_created: Optional[datetime]
    total_disbursement_quantity: Optional[dict] = None
    average_entitlement_per_registrant: Optional[dict] = None


class BeneficiaryListSummaryPayload(BaseModel):
    beneficiary_list_summary: BeneficiaryListSummary
    registry_summary: Optional[Any] = None
