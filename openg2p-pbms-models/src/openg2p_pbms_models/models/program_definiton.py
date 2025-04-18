from enum import Enum

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


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


class G2PProgramDefinition(BaseORMModel):
    __tablename__ = "g2p_program_definition"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_mnemonic = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=True)
    delivery_id = mapped_column(Integer, nullable=False)
    target_registry_type = mapped_column(String, nullable=False)
    program_status = mapped_column(String, nullable=False)
    max_quantity = mapped_column(Float, nullable=True)
    disbursement_frequency = mapped_column(
        SqlEnum(DisbursementFrequency),
        nullable=True,
        default=DisbursementFrequency.OnDemand,
    )
