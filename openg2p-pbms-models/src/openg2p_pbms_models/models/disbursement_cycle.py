from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel
from .status_enum import StatusEnum


class G2PDisbursementCycle(BaseORMModel):
    __tablename__ = "g2p_disbursement_cycle"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id = mapped_column(
        Integer, ForeignKey("g2p_program_definition.id"), nullable=False
    )
    cycle_mnemonic = mapped_column(String, nullable=False)
    bridge_envelope_id = mapped_column(String, nullable=True)
    # target_registry = mapped_column(String, nullable=True)
    envelope_creation_status = mapped_column(
        String, nullable=False, default=StatusEnum.PENDING.value
    )
    batch_creation_status = mapped_column(
        String, nullable=False, default=StatusEnum.NOT_APPLICABLE.value
    )
    approved_for_disbursement = mapped_column(Boolean, default=False, nullable=False)
    creation_date = mapped_column(DateTime, default=None, nullable=True)
    envelope_creation_latest_error_code = mapped_column(String, nullable=True)
    envelope_creation_attempts = mapped_column(Integer, default=0)
    batch_creation_latest_error_code = mapped_column(String, nullable=True)
    batch_creation_attempts = mapped_column(Integer, default=0)
    disbursement_schedule_date = mapped_column(Date, nullable=False)
    envelope_creation_latest_timestamp = mapped_column(
        DateTime(), default=None, nullable=True
    )
    batch_creation_latest_timestamp = mapped_column(
        DateTime(), default=None, nullable=True
    )
