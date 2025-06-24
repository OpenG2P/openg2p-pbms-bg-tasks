from typing import Optional

from pydantic import BaseModel


class Disbursement(BaseModel):
    beneficiary_id: str
    disbursement_id: Optional[int] = None
    entitlement: float
