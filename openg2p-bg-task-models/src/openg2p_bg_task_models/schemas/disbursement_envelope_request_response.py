from typing import List, Optional

from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
)
from pydantic import BaseModel


# new
class DisbursementEnvelopeRequestPayload(BaseModel):
    beneficiary_list_id: str


class DisbursementEnvelopeResponsePayload(BaseModel):
    beneficiary_list_id: Optional[str] = None
    disbursement_envelopes: Optional[List[dict]] = None


class DisbursementEnvelopeRequestBody(G2PRequestBody):
    request_payload: DisbursementEnvelopeRequestPayload


class DisbursementEnvelopeResponseBody(G2PResponseBody):
    response_payload: DisbursementEnvelopeResponsePayload


class DisbursementEnvelopeRequest(G2PRequest):
    request_body: DisbursementEnvelopeRequestBody


class DisbursementEnvelopeResponse(G2PResponse):
    response_body: DisbursementEnvelopeResponseBody
