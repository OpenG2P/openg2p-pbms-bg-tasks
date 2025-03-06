from typing import Optional

from .eligibility_summary import EligibilitySummaryResponse


class EligibilitySummaryStudentResponse(EligibilitySummaryResponse):
    age_mean: Optional[float]
    age_quartile_25: Optional[float]
    age_quartile_50: Optional[float]
    age_quartile_75: Optional[float]
