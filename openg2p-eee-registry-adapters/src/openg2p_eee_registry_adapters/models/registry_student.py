from openg2p_pbms_models.models import G2PRegistry
from sqlalchemy import Date, String
from sqlalchemy.orm import mapped_column


class G2PStudentRegistry(G2PRegistry):
    __tablename__ = "g2p_student_registry"

    name = mapped_column(String, nullable=False)
    institution_name = mapped_column(String, nullable=True)
    date_of_birth = mapped_column(Date, nullable=True)
