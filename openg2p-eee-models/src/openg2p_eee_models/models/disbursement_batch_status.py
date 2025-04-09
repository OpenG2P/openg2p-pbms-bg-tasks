import enum

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import mapped_column


class StatusEnum(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"


class DisbursementBatch(BaseORMModel):
    __tablename__ = "disbursement_batches"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    disbursement_cycle_id = mapped_column(Integer, nullable=False, index=True)
    program_id = mapped_column(Integer, nullable=False, index=True)
    bridge_envelope_id = mapped_column(String, nullable=False, index=True)
    pbms_request_id = mapped_column(String, nullable=False, index=True)
    registrant_ids = mapped_column(JSON, nullable=False)
    disbursement_status = mapped_column(
        String, nullable=False, default=StatusEnum.PENDING.value
    )
    bridge_disbursement_error_code = mapped_column(String, nullable=True)
    bridge_disbursement_status_attempts = mapped_column(Integer, default=0)
    bridge_disbursement_status_latest_timestamp = mapped_column(
        DateTime(), default=None, nullable=True
    )
