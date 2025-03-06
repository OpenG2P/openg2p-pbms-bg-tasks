from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EligibilitySummaryFarmerResponse(BaseModel):
    id: int
    program_id: int
    program_mnemonic: str
    target_registry_type: str
    eligibility_request_id: int
    number_of_registrants: int
    date_created: Optional[datetime]
    land_holding_mean: Optional[float]
    land_holding_quartile_25: Optional[float]
    land_holding_quartile_50: Optional[float]
    land_holding_quartile_75: Optional[float]
    annual_income_mean: Optional[float]
    annual_income_quartile_25: Optional[float]
    annual_income_quartile_50: Optional[float]
    annual_income_quartile_75: Optional[float]
