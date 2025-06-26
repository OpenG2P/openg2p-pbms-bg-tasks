from typing import Optional

from pydantic import BaseModel

from .beneficiary_list_summary import EEESummaryPayload


class RegistrySummaryStudentPayload(BaseModel):
    age_mean: Optional[str]
    age_quartile_25: Optional[str]
    age_quartile_50: Optional[str]
    age_quartile_75: Optional[str]
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


class EEESummaryStudentPayload(EEESummaryPayload):
    registry_summary: RegistrySummaryStudentPayload
