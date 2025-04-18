from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PDeliveryCodes(BaseORMModel):
    __tablename__ = "g2p_delivery_codes"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    delivery_mnemonic = mapped_column(String, primary_key=True)
    delivery_type = mapped_column(String, nullable=False)
    delivery_classification_id = mapped_column(String, nullable=False)
    delivery_description = mapped_column(String, nullable=True)
    measurement_unit = mapped_column(
        String, nullable=True
    )  # TODO Add a separate unit for currency ISO
