from typing import Optional

from pydantic import BaseModel

from .beneficiary_list_summary import BeneficiaryListSummaryPayload


class BeneficiaryListSummaryStudent(BaseModel):
    age_mean: Optional[str] = None
    age_q1: Optional[str] = None
    age_q2: Optional[str] = None
    age_q3: Optional[str] = None
    average_entitlement_female: Optional[dict] = None
    average_entitlement_male: Optional[dict] = None
    entitlement_amount_q1: Optional[dict] = None
    entitlement_amount_q2: Optional[dict] = None
    entitlement_amount_q3: Optional[dict] = None
    entitlement_amount_male_q1: Optional[dict] = None
    entitlement_amount_male_q2: Optional[dict] = None
    entitlement_amount_male_q3: Optional[dict] = None
    entitlement_amount_female_q1: Optional[dict] = None
    entitlement_amount_female_q2: Optional[dict] = None
    entitlement_amount_female_q3: Optional[dict] = None


class BeneficiaryListSummaryStudentPayload(BeneficiaryListSummaryPayload):
    registry_summary: BeneficiaryListSummaryStudent
