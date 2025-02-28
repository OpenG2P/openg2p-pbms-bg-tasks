from sqlalchemy import Float
from sqlalchemy.orm import mapped_column

from .eligibility_summary import G2PEligibilitySummary


class G2PEligibilitySummaryStudent(G2PEligibilitySummary):
    __tablename__ = "g2p_eligibility_summary_student"

    age_mean = mapped_column(Float, nullable=True)
    age_quartile_25 = mapped_column(Float, nullable=True)
    age_quartile_50 = mapped_column(Float, nullable=True)
    age_quartile_75 = mapped_column(Float, nullable=True)
