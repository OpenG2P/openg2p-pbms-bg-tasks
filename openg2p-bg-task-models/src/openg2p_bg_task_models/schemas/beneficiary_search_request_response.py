from typing import List, Optional

from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PResponse,
    G2PResponseBody,
)
from pydantic import BaseModel


class BeneficiarySearchRequestPayload(BaseModel):
    beneficiary_list_id: str
    target_registry: str
    # page: int
    # page_size: int
    # search_query: str
    # order_by: str


class BeneficiarySearchResponsePayload(BaseModel):
    beneficiary_count: int
    # page: int
    # page_size: int
    beneficiaries: Optional[List[object]] = None


class BeneficiarySearchRequestBody(G2PRequestBody):
    request_payload: BeneficiarySearchRequestPayload


class BeneficiarySearchResponseBody(G2PResponseBody):
    response_payload: BeneficiarySearchResponsePayload


class BeneficiarySearchRequest(G2PRequest):
    request_body: BeneficiarySearchRequestBody


class BeneficiarySearchResponse(G2PResponse):
    response_body: BeneficiarySearchResponseBody
