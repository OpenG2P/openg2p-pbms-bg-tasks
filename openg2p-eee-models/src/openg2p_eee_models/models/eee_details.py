from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import mapped_column

from .status_enum import StatusEnum


class EEEDetails(BaseORMModel):
    __tablename__ = "eee_details"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    pbms_request_id = mapped_column(String, nullable=False)
    registrant_details = mapped_column(JSON, nullable=False)
    number_of_registrants = mapped_column(Integer, nullable=False)
    entitlement_status = mapped_column(String, nullable=False, default=StatusEnum.PENDING.value)
