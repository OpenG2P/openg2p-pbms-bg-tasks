from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from .base import BaseORMModel


class G2PEligibilityRuleDefinition(BaseORMModel):
    __tablename__ = "g2p_eligibility_rule_definition"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    mnemonic = mapped_column(String, nullable=False, unique=True)
    description = mapped_column(String, nullable=True)
    program_id = mapped_column(
        Integer, ForeignKey("g2p_program_definition.id"), nullable=False
    )
    target_registry_type = mapped_column(String, nullable=False)
    pbms_domain = mapped_column(String, nullable=False)
    sql_query = mapped_column(String, nullable=True)
