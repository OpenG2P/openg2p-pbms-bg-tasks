from enum import Enum

from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class G2PRegistry(BaseORMModel):
    __abstract__ = True

    internal_record_id = mapped_column(String, nullable=True, primary_key=True)
