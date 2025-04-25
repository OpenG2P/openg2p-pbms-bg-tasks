from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class ProgramStatus(Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


class DisbursementFrequency(Enum):
    Daily = "Daily"
    Weekly = "Weekly"
    Fortnightly = "Fortnightly"
    Monthly = "Monthly"
    BiMonthly = "BiMonthly"
    Quarterly = "Quarterly"
    SemiAnnually = "SemiAnnually"
    Annually = "Annually"
    OnDemand = "OnDemand"


class BeneficiaryList(Enum):
    latest_always = "latest_always"
    labeled = "labeled"


class G2PProgramDefinition(BaseORMModel):
    __tablename__ = "g2p_program_definition"

    id = mapped_column(Integer, primary_key=True)
    program_mnemonic = mapped_column(String, nullable=False)
    description = mapped_column(String)
    benefit_code_id = mapped_column(
        Integer, ForeignKey("g2p_benefit_codes.id"), nullable=True
    )
    max_quantity = mapped_column(Integer)

    target_registry_type = mapped_column(String, nullable=False)
    program_status = mapped_column(SqlEnum(ProgramStatus), nullable=False)
    disbursement_frequency = mapped_column(
        SqlEnum(DisbursementFrequency), nullable=True
    )

    disbursement_day_of_month = mapped_column(Integer, nullable=True)
    disbursement_day_of_week = mapped_column(String, nullable=True)
    disbursement_start_month = mapped_column(String, nullable=True)
    beneficiary_list = mapped_column(SqlEnum(BeneficiaryList), nullable=False)

    distribution_through_agencies = mapped_column(Boolean, default=True)
    only_direct_credit_allowed = mapped_column(Boolean, default=True)
    on_demand_cycle_allowed = mapped_column(Boolean, default=False)

    show_disbursement_day_of_week = mapped_column(Boolean, default=False)
    show_disbursement_day_of_month = mapped_column(Boolean, default=False)
    show_disbursement_start_month = mapped_column(Boolean, default=False)
    show_label_for_beneficiary_list = mapped_column(Boolean, default=False)

    label_for_beneficiary_list_id = mapped_column(
        Integer, ForeignKey("g2p_que_eee_request.id"), nullable=True
    )

    create_uid = mapped_column(Integer)
    write_uid = mapped_column(Integer)
    create_date = mapped_column(DateTime)
    write_date = mapped_column(DateTime)
