from typing import List, Optional

from openg2p_g2pconnect_common_lib.schemas import (
    Request,
    SyncResponse,
)
from pydantic import BaseModel


class EEEBeneficiarySearchRequestPayload(BaseModel):
    beneficiary_list_id: str
    target_registry_type: str
    page: int
    page_size: int
    search_query: str
    order_by: str


class EEEBeneficiarySearchResponsePayload(BaseModel):
    total_beneficiary_count: int
    page: int
    page_size: int
    beneficiaries: Optional[List[object]] = None


class EEEBeneficiarySearchRequest(Request):
    message: EEEBeneficiarySearchRequestPayload


class EEEBeneficiarySearchResponse(SyncResponse):
    message: EEEBeneficiarySearchResponsePayload
