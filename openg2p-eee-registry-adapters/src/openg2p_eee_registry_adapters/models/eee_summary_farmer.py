from openg2p_eee_models.models import EEESummary
from sqlalchemy import Float, String
from sqlalchemy.orm import mapped_column


class EEESummaryFarmer(EEESummary):
    __tablename__ = "eee_summary_farmer"

    land_holding_quartile_25 = mapped_column(Float, nullable=True, default=0)
    land_holding_quartile_50 = mapped_column(Float, nullable=True, default=0)
    land_holding_quartile_75 = mapped_column(Float, nullable=True, default=0)
    land_holding_mean = mapped_column(Float, nullable=True, default=0)
    land_holding_units = mapped_column(String, nullable=False, default='acres')

    annual_income_quartile_25 = mapped_column(Float, nullable=True, default=0)
    annual_income_quartile_50 = mapped_column(Float, nullable=True, default=0)
    annual_income_quartile_75 = mapped_column(Float, nullable=True, default=0)
    annual_income_mean = mapped_column(Float, nullable=True, default=0)
    annual_income_units = mapped_column(String, nullable=False, default='INR')

    average_entitlement_female = mapped_column(Float, nullable=True, default=0)
    average_entitlement_male = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_male_q1 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_male_q2 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_male_q3 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_female_q1 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_female_q2 = mapped_column(Float, nullable=True, default=0)
    entitlement_amount_female_q3 = mapped_column(Float, nullable=True, default=0)
    entitlement_units = mapped_column(String, nullable=False, default='INR')
