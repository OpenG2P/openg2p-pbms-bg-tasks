from openg2p_g2pconnect_common_lib.schemas import (
    Request,
    SyncResponse,
)
from pydantic import BaseModel


class SummaryRequestPayload(BaseModel):
    beneficiary_list_id: str
    target_registry: str


class SummaryRequest(Request):
    message: SummaryRequestPayload


class SummaryResponse(SyncResponse):
    message: object
