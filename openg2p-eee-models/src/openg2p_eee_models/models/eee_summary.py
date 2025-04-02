from datetime import datetime, timezone

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import mapped_column


class EEESummary(BaseORMModel):
    __abstract__ = True

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id = mapped_column(Integer, nullable=False)
    program_mnemonic = mapped_column(String, nullable=False)
    target_registry_type = mapped_column(String, nullable=False)
    pbms_request_id = mapped_column(String, index=True, unique=True, nullable=False)
    number_of_registrants = mapped_column(Integer, nullable=False)

    total_entitlement_amount = mapped_column(Float, nullable=True)
    average_entitlement_per_person = mapped_column(Float, nullable=True)
    entitlement_amount_q1 = mapped_column(Float, nullable=True)
    entitlement_amount_q2 = mapped_column(Float, nullable=True)
    entitlement_amount_q3 = mapped_column(Float, nullable=True)

    date_created = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
