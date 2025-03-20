from openg2p_eee_models.models import EEESummary
from sqlalchemy import Float
from sqlalchemy.orm import mapped_column


class EEESummaryStudent(EEESummary):
    __tablename__ = "g2p_eee_summary_student"

    age_mean = mapped_column(Float, nullable=True)
    age_quartile_25 = mapped_column(Float, nullable=True)
    age_quartile_50 = mapped_column(Float, nullable=True)
    age_quartile_75 = mapped_column(Float, nullable=True)

    average_entitlement_female = mapped_column(Float, nullable=True)
    average_entitlement_male = mapped_column(Float, nullable=True)
    entitlement_amount_male_q1 = mapped_column(Float, nullable=True)
    entitlement_amount_male_q2 = mapped_column(Float, nullable=True)
    entitlement_amount_male_q3 = mapped_column(Float, nullable=True)
    entitlement_amount_female_q1 = mapped_column(Float, nullable=True)
    entitlement_amount_female_q2 = mapped_column(Float, nullable=True)
    entitlement_amount_female_q3 = mapped_column(Float, nullable=True)
