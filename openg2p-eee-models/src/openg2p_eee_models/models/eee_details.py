from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import mapped_column


class EEEDetails(BaseORMModel):
    __tablename__ = "g2p_eee_details"

    pbms_request_id = mapped_column(String, primary_key=True)
    registrant_id = mapped_column(Integer, primary_key=True)
    quantity = mapped_column(Float, nullable=False)
