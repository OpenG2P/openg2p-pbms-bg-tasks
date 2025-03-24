import enum
from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import mapped_column


class EnumStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"


class G2PQueEEERequest(BaseORMModel):
    __tablename__ = "g2p_que_eee_request"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    pbms_request_id = mapped_column(String, index=True, unique=True, nullable=False)
    program_id = mapped_column(
        Integer, ForeignKey("g2p_program_definition.id"), nullable=False
    )
    brief = mapped_column(Text, nullable=True)
    eligibility_process_status = mapped_column(
        String, nullable=False, default=EnumStatus.PENDING.value
    )
    entitlement_process_status = mapped_column(
        String, nullable=False, default=EnumStatus.NOT_APPLICABLE.value
    )
    creation_date = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_date = mapped_column(DateTime, default=None, nullable=True)
