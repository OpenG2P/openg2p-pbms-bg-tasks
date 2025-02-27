import enum
from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import mapped_column


class G2PEligibilityDetails(BaseORMModel):
    __tablename__ = "g2p_eligibility_details"

    eligibility_list_id = mapped_column(Integer, ForeignKey("g2p_eligibility_list.id"), primary_key=True)
    registrant_id = mapped_column(Integer, ForeignKey("g2p_registry.id"), primary_key=True)
