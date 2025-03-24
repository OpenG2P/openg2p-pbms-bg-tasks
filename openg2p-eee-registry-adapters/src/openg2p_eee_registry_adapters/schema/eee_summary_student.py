from typing import Optional

from pydantic import BaseModel

from .eee_summary import EEESummaryPayload


class EligibilitySummaryStudentPayload(BaseModel):
    age_mean: Optional[float]
    age_quartile_25: Optional[float]
    age_quartile_50: Optional[float]
    age_quartile_75: Optional[float]


class EntitlementSummaryStudentPayload(BaseModel):
    total_entitlement_amount: Optional[float] = None
    average_entitlement_per_person: Optional[float] = None
    average_entitlement_female: Optional[float] = None
    average_entitlement_male: Optional[float] = None
    entitlement_amount_q1: Optional[float] = None
    entitlement_amount_q2: Optional[float] = None
    entitlement_amount_q3: Optional[float] = None
    entitlement_amount_male_q1: Optional[float] = None
    entitlement_amount_male_q2: Optional[float] = None
    entitlement_amount_male_q3: Optional[float] = None
    entitlement_amount_female_q1: Optional[float] = None
    entitlement_amount_female_q2: Optional[float] = None
    entitlement_amount_female_q3: Optional[float] = None


class EEESummaryStudentPayload(EEESummaryPayload):
    eligibility_summary: EligibilitySummaryStudentPayload
    entitlement_summary: EntitlementSummaryStudentPayload
