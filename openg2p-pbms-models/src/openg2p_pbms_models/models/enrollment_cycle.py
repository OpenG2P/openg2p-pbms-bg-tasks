from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from .base import BaseORMModel


class G2PEnrollmentCycle(BaseORMModel):
    __tablename__ = "g2p_enrollment_cycle"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    enrollment_cycle_id = mapped_column(String, nullable=True)
    cycle_number = mapped_column(Integer, nullable=False)
    program_id = mapped_column(
        Integer, ForeignKey("g2p_program_definition.id"), nullable=False
    )
    enrollment_start_date = mapped_column(Date, nullable=False)
    enrollment_end_date = mapped_column(Date, nullable=False)
    disbursement_start_date = mapped_column(Date, nullable=False)
    disbursement_end_date = mapped_column(Date, nullable=False)

    beneficiary_list_ids = relationship(
        "G2PBeneficiaryList", backref="enrollment_cycle"
    )
