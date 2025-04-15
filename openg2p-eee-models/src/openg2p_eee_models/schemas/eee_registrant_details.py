from pydantic import BaseModel


class RegistrantDetails(BaseModel):
    registrant_id: str
    entitlement_quantity: float
