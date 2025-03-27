from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import mapped_column


class G2PRegistry(BaseORMModel):
    __abstract__ = True

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    unique_id = mapped_column(String, nullable=True)
    registration_date = mapped_column(
        DateTime, default=datetime.now(datetime.timezone.utc), nullable=False
    )
