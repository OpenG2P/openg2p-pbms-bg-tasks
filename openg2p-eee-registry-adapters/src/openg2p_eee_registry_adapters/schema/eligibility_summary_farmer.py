from typing import Optional

from .eligibility_summary import EligibilitySummaryPayload


class EligibilitySummaryFarmerPayload(EligibilitySummaryPayload):
    land_holding_mean: Optional[float]
    land_holding_quartile_25: Optional[float]
    land_holding_quartile_50: Optional[float]
    land_holding_quartile_75: Optional[float]
    annual_income_mean: Optional[float]
    annual_income_quartile_25: Optional[float]
    annual_income_quartile_50: Optional[float]
    annual_income_quartile_75: Optional[float]
