import uuid

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import mapped_column

from .status_enum import StatusEnum


class BeneficiaryListDetails(BaseORMModel):
    __tablename__ = "beneficiary_list_details"

    id = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )
    beneficiary_list_id = mapped_column(String, nullable=False, index=True)
    registrant_details = mapped_column(JSON, nullable=False)
    number_of_registrants = mapped_column(Integer, nullable=False)
    entitlement_process_status = mapped_column(
        String, nullable=False, default=StatusEnum.NOT_APPLICABLE.value
    )
