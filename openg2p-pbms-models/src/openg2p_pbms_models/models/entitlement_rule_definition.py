from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PEntitlementRuleDefinition(BaseORMModel):
    __tablename__ = "g2p_entitlement_rule_definition"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    mnemonic = mapped_column(String, nullable=False, unique=True)
    description = mapped_column(String, nullable=True)
    target_registry_type = mapped_column(String, nullable=False)
    program_id = mapped_column(Integer, nullable=False, index=True)
    quantity = mapped_column(Float, nullable=False)
    pbms_domain = mapped_column(String, nullable=True)
    sql_query = mapped_column(String, nullable=False)
