from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class G2PRegistry(BaseORMModel):
    __abstract__ = True

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    unique_id = mapped_column(String, nullable=True)
    registration_date = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    gender = mapped_column(
        String,
        nullable=False,
        default=Gender.OTHER.value,
    )
