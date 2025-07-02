from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PEntitlementRuleDefinition(BaseORMModel):
    __tablename__ = "g2p_entitlement_rule_definition"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    mnemonic = mapped_column(String, nullable=False, unique=True)
    description = mapped_column(String, nullable=True)
    program_id = mapped_column(Integer, nullable=False, index=True)
    benefit_code_id = mapped_column(
        Integer, ForeignKey("g2p_benefit_codes.id"), nullable=True
    )
    # measurement_unit = mapped_column(String, nullable=True)
    multiplier = mapped_column(String, nullable=True)
    # allowed_multipliers = mapped_column(String, nullable=True)
    quantity = mapped_column(Float, nullable=False)
    pbms_domain = mapped_column(String, nullable=False)
    sql_query = mapped_column(String, nullable=False)
