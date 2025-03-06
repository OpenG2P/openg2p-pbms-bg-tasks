from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EligibilitySummaryStudentResponse(BaseModel):
    id: int
    program_id: int
    program_mnemonic: str
    target_registry_type: str
    eligibility_request_id: int
    number_of_registrants: int
    date_created: Optional[datetime]
    age_mean: Optional[float]
    age_quartile_25: Optional[float]
    age_quartile_50: Optional[float]
    age_quartile_75: Optional[float]
