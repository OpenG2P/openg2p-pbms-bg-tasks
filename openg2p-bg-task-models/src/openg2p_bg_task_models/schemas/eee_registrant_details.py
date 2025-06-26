from typing import Dict

from pydantic import BaseModel


class RegistrantDetails(BaseModel):
    registrant_id: str
    entitlement: Dict[int, float]
