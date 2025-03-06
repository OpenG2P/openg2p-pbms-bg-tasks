from openg2p_g2pconnect_common_lib.schemas import (
    Request,
    SyncResponse,
)
from pydantic import BaseModel


class EEEBeneficiarySearchRequestPayload(BaseModel):
    registry_type: str
    page: int
    page_size: int
    search_query: str
    order_by: str


class EEEBeneficiarySearchRequest(Request):
    message: EEEBeneficiarySearchRequestPayload


class EEEBeneficiarySearchResponse(SyncResponse):
    message: object
