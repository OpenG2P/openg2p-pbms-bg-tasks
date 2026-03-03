from typing import List, Optional

from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
)
from pydantic import BaseModel


class DisbursementBatchRequestPayload(BaseModel):
    beneficiary_list_id: str


class DisbursementBatchResponsePayload(BaseModel):
    beneficiary_list_id: Optional[str] = None
    disbursement_batches: List[dict]


class DisbursementBatchRequestBody(G2PRequestBody):
    request_payload: DisbursementBatchRequestPayload


class DisbursementBatchResponseBody(G2PResponseBody):
    response_payload: DisbursementBatchResponsePayload


class DisbursementBatchRequest(G2PRequest):
    request_body: DisbursementBatchRequestBody


class DisbursementBatchResponse(G2PResponse):
    response_body: DisbursementBatchResponseBody
