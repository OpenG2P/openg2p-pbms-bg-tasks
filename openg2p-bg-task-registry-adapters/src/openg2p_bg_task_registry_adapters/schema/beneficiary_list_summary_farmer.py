from typing import Optional

from pydantic import BaseModel

from .beneficiary_list_summary import BeneficiaryListSummaryPayload


class BeneficiaryListSummaryFarmer(BaseModel):
    land_holding_mean: Optional[str] = None
    land_holding_quartile_75: Optional[str] = None
    land_holding_quartile_50: Optional[str] = None
    land_holding_quartile_25: Optional[str] = None
    annual_income_mean: Optional[str] = None
    annual_income_quartile_75: Optional[str] = None
    annual_income_quartile_50: Optional[str] = None
    annual_income_quartile_25: Optional[str] = None
    average_entitlement_female: Optional[dict] = None
    average_entitlement_male: Optional[dict] = None
    entitlement_amount_75: Optional[dict] = None
    entitlement_amount_50: Optional[dict] = None
    entitlement_amount_25: Optional[dict] = None
    entitlement_amount_male_75: Optional[dict] = None
    entitlement_amount_male_50: Optional[dict] = None
    entitlement_amount_male_25: Optional[dict] = None
    entitlement_amount_female_75: Optional[dict] = None
    entitlement_amount_female_50: Optional[dict] = None
    entitlement_amount_female_25: Optional[dict] = None


class BeneficiaryListSummaryFarmerPayload(BeneficiaryListSummaryPayload):
    registry_summary: BeneficiaryListSummaryFarmer
