from typing import Optional

from .eligibility_summary import EligibilitySummaryPayload


class EligibilitySummaryStudentPayload(EligibilitySummaryPayload):
    age_mean: Optional[float]
    age_quartile_25: Optional[float]
    age_quartile_50: Optional[float]
    age_quartile_75: Optional[float]
