from sqlalchemy import Float
from sqlalchemy.orm import mapped_column

from .eligibility_summary import G2PEligibilitySummary


class G2PEligibilitySummaryFarmer(G2PEligibilitySummary):
    __tablename__ = "g2p_eligibility_summary_farmer"

    land_holding_quartile_25 = mapped_column(Float, nullable=True)
    land_holding_quartile_50 = mapped_column(Float, nullable=True)
    land_holding_quartile_75 = mapped_column(Float, nullable=True)
    land_holding_mean = mapped_column(Float, nullable=True)
    annual_income_quartile_25 = mapped_column(Float, nullable=True)
    annual_income_quartile_50 = mapped_column(Float, nullable=True)
    annual_income_quartile_75 = mapped_column(Float, nullable=True)
    annual_income_mean = mapped_column(Float, nullable=True)
