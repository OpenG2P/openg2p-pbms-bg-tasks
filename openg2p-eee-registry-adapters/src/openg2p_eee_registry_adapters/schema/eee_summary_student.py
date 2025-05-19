from typing import Optional

from pydantic import BaseModel

from .eee_summary import EEESummaryPayload


# TODO: change q1 -> 25 ...
class RegistrySummaryStudentPayload(BaseModel):
    age_mean: Optional[str]
    age_quartile_25: Optional[str]
    age_quartile_50: Optional[str]
    age_quartile_75: Optional[str]
    average_entitlement_female: Optional[str] = None
    average_entitlement_male: Optional[str] = None
    entitlement_amount_q1: Optional[str] = None
    entitlement_amount_q2: Optional[str] = None
    entitlement_amount_q3: Optional[str] = None
    entitlement_amount_male_q1: Optional[str] = None
    entitlement_amount_male_q2: Optional[str] = None
    entitlement_amount_male_q3: Optional[str] = None
    entitlement_amount_female_q1: Optional[str] = None
    entitlement_amount_female_q2: Optional[str] = None
    entitlement_amount_female_q3: Optional[str] = None


class EEESummaryStudentPayload(EEESummaryPayload):
    registry_summary: RegistrySummaryStudentPayload
