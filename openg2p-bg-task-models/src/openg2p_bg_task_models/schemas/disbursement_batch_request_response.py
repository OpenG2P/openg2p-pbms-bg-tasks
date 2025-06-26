from typing import List

from openg2p_g2pconnect_common_lib.schemas import (
    Request,
    SyncResponse,
)
from pydantic import BaseModel


class DisbursementBatchRequestPayload(BaseModel):
    beneficiary_list_id: str


class DisbursementBatchResponsePayload(BaseModel):
    beneficiary_list_id: str
    disbursement_envelopes: List[dict]


class DisbursementBatchRequest(Request):
    message: DisbursementBatchRequestPayload


class DisbursementBatchResponse(SyncResponse):
    message: DisbursementBatchResponsePayload
