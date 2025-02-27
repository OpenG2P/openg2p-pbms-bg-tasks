import enum
from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import mapped_column


class EnumStatus(enum.Enum):
    PENDING = "pending"
    COMPLETE = "complete"


class G2PQueEligibilityRequest(BaseORMModel):
    __tablename__ = "g2p_que_eligibility_request"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id = mapped_column(Integer, ForeignKey("g2p_program_definition.id"), nullable=False)
    brief = mapped_column(Text, nullable=True)
    sql_query_json = mapped_column(Text, nullable=False)
    enumeration_status = mapped_column(String, nullable=False, default=EnumStatus.PENDING.value)
    creation_date = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_date = mapped_column(DateTime, default=None, nullable=True)
