from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import mapped_column
import enum

class StatusEnum(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"

class DisbursementBatchStatus(BaseORMModel):
    __tablename__ = "disbursement_batch_status"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    disbursement_cycle_id = mapped_column(Integer, nullable=False, index=True)
    program_id = mapped_column(Integer, nullable=False, index=True)
    bridge_envelope_id = mapped_column(String, nullable=False, index=True)
    pbms_request_id = mapped_column(String, nullable=False, index=True)
    registrant_ids = mapped_column(JSON, nullable=False)
    disbursement_status = mapped_column(String, nullable=False, default=StatusEnum.PENDING.value)
    disbursement_latest_error_code = mapped_column(String, nullable=True)
    disbursement_attempts = mapped_column(Integer, default=0)
    disbursement_latest_timestamp = mapped_column(
        DateTime(), default=None, nullable=True
    )
    
