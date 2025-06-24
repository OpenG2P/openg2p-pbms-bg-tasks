import uuid

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import mapped_column

from .status_enum import StatusEnum


class DisbursementBatch(BaseORMModel):
    __tablename__ = "disbursement_batch"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    disbursement_batch_id = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )
    beneficiary_list_id = mapped_column(String, nullable=False)
    disbursement_cycle_id = mapped_column(String, nullable=False)
    beneficiary_list_details_id = mapped_column(Integer, nullable=False)
    disbursement_envelope_id = mapped_column(String, nullable=False)
    disbursements = mapped_column(JSON, nullable=False)
    disbursement_status = mapped_column(
        String, nullable=False, default=StatusEnum.PENDING.value
    )
    # response_error_codes = mapped_column(String, nullable=True)
