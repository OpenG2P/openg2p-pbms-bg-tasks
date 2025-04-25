from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PBenefitCodes(BaseORMModel):
    __tablename__ = "g2p_benefit_codes"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    benefit_mnemonic = mapped_column(String, primary_key=True)
    benefit_type = mapped_column(String, nullable=False)
    benefit_classification_id = mapped_column(String, nullable=False)
    benefit_description = mapped_column(String, nullable=True)
    measurement_unit = mapped_column(
        String, nullable=True
    )  # TODO Add a separate unit for currency ISO
