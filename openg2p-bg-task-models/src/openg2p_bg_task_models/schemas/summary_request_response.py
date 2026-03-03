from typing import Optional

from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
)
from pydantic import BaseModel


class SummaryRequestPayload(BaseModel):
    beneficiary_list_id: str
    target_registry: str

class SummaryResponsePayloadBase(BaseModel):
    pass

class SummaryResponsePayload(BaseModel):
    beneficiary_list_id: Optional[str] = None
    summary: Optional[SummaryResponsePayloadBase] = None


class SummaryRequestBody(G2PRequestBody):
    request_payload: SummaryRequestPayload


class SummaryResponseBody(G2PResponseBody):
    response_payload: SummaryResponsePayload


class SummaryRequest(G2PRequest):
    request_body: SummaryRequestBody


class SummaryResponse(G2PResponse):
    response_body: SummaryResponseBody
