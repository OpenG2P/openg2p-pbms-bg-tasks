import enum

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import mapped_column


class BenefitType(enum.Enum):
    COMMODITY = "COMMODITY"
    SERVICE = "SERVICE"
    CASH = "CASH"
    COMBINATION = "COMBINATION"


class CashDistributionMode(enum.Enum):
    PHYSICAL = "PHYSICAL"
    DIGITAL = "DIGITAL"


class DisbursementEnvelope(BaseORMModel):
    __tablename__ = "disbursement_envelope"

    disbursement_envelope_id = mapped_column(String, primary_key=True, nullable=False)
    benefit_program_mnemonic = mapped_column(String, nullable=False)
    benefit_code_id = mapped_column(Integer, nullable=False)
    beneficiary_list_id = mapped_column(String, nullable=False)
    benefit_type = mapped_column(SqlEnum(BenefitType), nullable=False)
    cash_distribution_mode = mapped_column(
        SqlEnum(CashDistributionMode), nullable=False
    )
    disbursement_cycle_id = mapped_column(String, nullable=False)
    cycle_code_mnemonic = mapped_column(String, nullable=False)
    number_of_beneficiaries = mapped_column(Integer, nullable=False)
    number_of_disbursements = mapped_column(Integer, nullable=False)
    total_disbursement_quantity = mapped_column(Float, nullable=False)
    measurement_unit = mapped_column(String, nullable=False)
    disbursement_schedule_date = mapped_column(DateTime, nullable=False)
