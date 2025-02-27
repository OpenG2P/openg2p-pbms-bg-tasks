from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column


class G2PProgramDefinition(BaseORMModel):
    __tablename__ = "g2p_program_definition"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_mnemonic = mapped_column(String, nullable=False)
    target_registry_type = mapped_column(String, nullable=False)
