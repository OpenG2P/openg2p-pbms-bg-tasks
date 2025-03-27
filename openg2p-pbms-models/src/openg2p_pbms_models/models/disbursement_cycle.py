from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column
from sqlalchemy import DateTime
from datetime import datetime

from .status_enum import StatusEnum


class G2PDisbursementCycle(BaseORMModel):
    __tablename__ = "g2p_disbursement_cycle"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id = mapped_column(Integer, nullable=False)
    cycle_mnemonic = mapped_column(String, nullable=False)
    pbms_request_id = mapped_column(String, nullable=False)
    bridge_envelope_id = mapped_column(String, nullable=True)
    envelope_creation_status = mapped_column(String, nullable=False, default=StatusEnum.PENDING.value)
    batch_creation_status = mapped_column(String, nullable=False, default=StatusEnum.NOT_APPLICABLE.value)
    envelope_creation_latest_error_code = mapped_column(String, nullable=True)
    envelope_creation_attempts = mapped_column(Integer, default=0)
    batch_creation_latest_error_code = mapped_column(String, nullable=True)
    batch_creation_attempts = mapped_column(Integer, default=0)
    envelope_creation_latest_timestamp = mapped_column(
        DateTime(), default=None, nullable=True
    )
    batch_creation_latest_timestamp = mapped_column(
        DateTime(), default=None, nullable=True
    )

