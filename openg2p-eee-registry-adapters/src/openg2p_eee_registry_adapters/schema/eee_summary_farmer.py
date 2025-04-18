from typing import Optional

from pydantic import BaseModel

from .eee_summary import EEESummaryPayload


class RegistrySummaryFarmerPayload(BaseModel):
    land_holding_mean: Optional[float]
    land_holding_quartile_25: Optional[float]
    land_holding_quartile_50: Optional[float]
    land_holding_quartile_75: Optional[float]
    annual_income_mean: Optional[float]
    annual_income_quartile_25: Optional[float]
    annual_income_quartile_50: Optional[float]
    annual_income_quartile_75: Optional[float]
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


class EEESummaryFarmerPayload(EEESummaryPayload):
    registry_summary: RegistrySummaryFarmerPayload
