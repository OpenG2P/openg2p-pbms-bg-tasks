from openg2p_eee_models.models import EEESummary
from sqlalchemy import Float
from sqlalchemy.orm import mapped_column


class EligibilitySummaryStudent(EEESummary):
    __tablename__ = "g2p_eligibility_summary_student"

    age_mean = mapped_column(Float, nullable=True)
    age_quartile_25 = mapped_column(Float, nullable=True)
    age_quartile_50 = mapped_column(Float, nullable=True)
    age_quartile_75 = mapped_column(Float, nullable=True)
