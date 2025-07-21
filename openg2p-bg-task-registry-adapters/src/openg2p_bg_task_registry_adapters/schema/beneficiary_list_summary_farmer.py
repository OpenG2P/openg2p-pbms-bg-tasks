from typing import Optional

from pydantic import BaseModel

from .beneficiary_list_summary import BeneficiaryListSummaryPayload


class BeneficiaryListSummaryFarmer(BaseModel):
    land_holding_mean: Optional[str] = None
    land_holding_q3: Optional[str] = None
    land_holding_q2: Optional[str] = None
    land_holding_q1: Optional[str] = None
    annual_income_mean: Optional[str] = None
    annual_income_q3: Optional[str] = None
    annual_income_q2: Optional[str] = None
    annual_income_q1: Optional[str] = None
    average_entitlement_female: Optional[dict] = None
    average_entitlement_male: Optional[dict] = None
    entitlement_amount_q3: Optional[dict] = None
    entitlement_amount_q2: Optional[dict] = None
    entitlement_amount_q1: Optional[dict] = None
    entitlement_amount_male_q3: Optional[dict] = None
    entitlement_amount_male_q2: Optional[dict] = None
    entitlement_amount_male_q1: Optional[dict] = None
    entitlement_amount_female_q3: Optional[dict] = None
    entitlement_amount_female_q2: Optional[dict] = None
    entitlement_amount_female_q1: Optional[dict] = None


class BeneficiaryListSummaryFarmerPayload(BeneficiaryListSummaryPayload):
    registry_summary: BeneficiaryListSummaryFarmer
