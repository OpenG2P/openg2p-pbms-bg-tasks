from openg2p_eee_models.models import EEESummary
from sqlalchemy import Float, String
from sqlalchemy.orm import mapped_column


class EEESummaryStudent(EEESummary):
    __tablename__ = "eee_summary_student"

    age_mean = mapped_column(Float, nullable=True, default=0)
    age_quartile_25 = mapped_column(Float, nullable=True, default=0)
    age_quartile_50 = mapped_column(Float, nullable=True, default=0)
    age_quartile_75 = mapped_column(Float, nullable=True, default=0)
    age_units = mapped_column(String, nullable=False, default="years")

    average_entitlement_female = mapped_column(Float, nullable=True, default=0)
    average_entitlement_male = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_male_q1 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_male_q2 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_male_q3 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_female_q1 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_female_q2 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_female_q3 = mapped_column(Float, nullable=True, default=0)
    entitlement_units = mapped_column(String, nullable=False, default="INR")
