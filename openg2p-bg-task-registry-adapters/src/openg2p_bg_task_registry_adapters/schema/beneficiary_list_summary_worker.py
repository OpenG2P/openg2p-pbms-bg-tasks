from typing import Optional

from pydantic import BaseModel

from .beneficiary_list_summary import BeneficiaryListSummaryPayload


class BeneficiaryListSummaryWorker(BaseModel):
    entitlement_amount_q3: Optional[dict] = None
    entitlement_amount_q2: Optional[dict] = None
    entitlement_amount_q1: Optional[dict] = None


class BeneficiaryListSummaryWorkerPayload(BeneficiaryListSummaryPayload):
    registry_summary: BeneficiaryListSummaryWorker
