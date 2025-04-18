from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import mapped_column

from .status_enum import StatusEnum


class Disbursement(BaseORMModel):
    __tablename__ = "bridge_disbursements"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    bridge_disbursement_id = mapped_column(String, nullable=False, index=True)
    disbursement_batch_id = mapped_column(Integer, index=True, nullable=False)
    registrant_id = mapped_column(String, nullable=False, index=True)
    bridge_downstream_status = mapped_column(
        String, nullable=False, default=StatusEnum.PENDING.value
    )
    bridge_downstream_error_code = mapped_column(String, nullable=True)
    bridge_polling_attempts = mapped_column(Integer, default=0)
    bridge_polling_latest_timestamp = mapped_column(
        DateTime(), default=None, nullable=True
    )
