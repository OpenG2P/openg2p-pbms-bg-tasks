from openg2p_g2pconnect_common_lib.schemas import (
    Request,
    SyncResponse,
)
from pydantic import BaseModel


class EEESummaryRequestPayload(BaseModel):
    beneficiary_list_id: str
    target_registry_type: str


class EEESummaryRequest(Request):
    message: EEESummaryRequestPayload


class EEESummaryResponse(SyncResponse):
    message: object
