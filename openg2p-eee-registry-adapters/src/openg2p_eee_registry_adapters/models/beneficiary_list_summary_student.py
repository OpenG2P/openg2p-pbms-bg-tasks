from openg2p_eee_models.models import BeneficiaryListSummary
from sqlalchemy import JSON, Float, String
from sqlalchemy.orm import mapped_column


class BeneficiaryListSummaryStudent(BeneficiaryListSummary):
    __tablename__ = "beneficiary_list_summary_student"

    age_mean = mapped_column(Float, nullable=True, default=0)
    age_quartile_25 = mapped_column(Float, nullable=True, default=0)
    age_quartile_50 = mapped_column(Float, nullable=True, default=0)
    age_quartile_75 = mapped_column(Float, nullable=True, default=0)
    age_units = mapped_column(String, nullable=False, default="years")

    average_entitlement_female = mapped_column(JSON, nullable=True)
    average_entitlement_male = mapped_column(JSON, nullable=True)
    entitlement_amount_male_q1 = mapped_column(JSON, nullable=True)
    entitlement_amount_male_q2 = mapped_column(JSON, nullable=True)
    entitlement_amount_male_q3 = mapped_column(JSON, nullable=True)
    entitlement_amount_female_q1 = mapped_column(JSON, nullable=True)
    entitlement_amount_female_q2 = mapped_column(JSON, nullable=True)
    entitlement_amount_female_q3 = mapped_column(JSON, nullable=True)
    entitlement_units = mapped_column(JSON, nullable=True)
