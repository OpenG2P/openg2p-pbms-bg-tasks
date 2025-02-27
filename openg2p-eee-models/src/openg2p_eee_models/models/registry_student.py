from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import mapped_column


class G2PStudentRegistry(BaseORMModel):
    __tablename__ = "g2p_student_registry"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    unique_id = mapped_column(String, nullable=True)
    registration_date = mapped_column(DateTime, default=datetime.utcnow(), nullable=False)
    name = mapped_column(String, nullable=False)
    institution_name = mapped_column(String, nullable=True)
    date_of_birth = mapped_column(DateTime, nullable=True)
