from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from .registry import G2PRegistryType


class G2PEligibilitySummaryStudent(BaseORMModel):
    __tablename__ = "g2p_eligibility_summary_student"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id = mapped_column(
        Integer, ForeignKey("g2p_program_definition.id"), nullable=False
    )
    program_mnemonic = mapped_column(String, nullable=False)
    target_registry_type = mapped_column(Enum(G2PRegistryType), nullable=False)
    eligibility_request_id = mapped_column(
        Integer, ForeignKey("g2p_que_eligibility_request.id"), nullable=False
    )
    number_of_registrants = mapped_column(Integer, nullable=False)
    date_created = mapped_column(DateTime, default=datetime.utcnow(), nullable=False)
    age_quartile_25 = mapped_column(Float, nullable=True)
    age_quartile_50 = mapped_column(Float, nullable=True)
    age_quartile_75 = mapped_column(Float, nullable=True)
