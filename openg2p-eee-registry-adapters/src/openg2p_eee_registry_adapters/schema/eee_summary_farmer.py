from typing import Optional

from pydantic import BaseModel

from .eee_summary import EEESummaryPayload


class RegistrySummaryFarmerPayload(BaseModel):
    land_holding_mean: Optional[str]
    land_holding_quartile_75: Optional[str]
    land_holding_quartile_50: Optional[str]
    land_holding_quartile_25: Optional[str]
    annual_income_mean: Optional[str]
    annual_income_quartile_75: Optional[str]
    annual_income_quartile_50: Optional[str]
    annual_income_quartile_25: Optional[str]
    average_entitlement_female: Optional[str] = None
    average_entitlement_male: Optional[str] = None
    entitlement_amount_75: Optional[str] = None
    entitlement_amount_50: Optional[str] = None
    entitlement_amount_25: Optional[str] = None
    entitlement_amount_male_75: Optional[str] = None
    entitlement_amount_male_50: Optional[str] = None
    entitlement_amount_male_25: Optional[str] = None
    entitlement_amount_female_75: Optional[str] = None
    entitlement_amount_female_50: Optional[str] = None
    entitlement_amount_female_25: Optional[str] = None


class EEESummaryFarmerPayload(EEESummaryPayload):
    registry_summary: RegistrySummaryFarmerPayload
