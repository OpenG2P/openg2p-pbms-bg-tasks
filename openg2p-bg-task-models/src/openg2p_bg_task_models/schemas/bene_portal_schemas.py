from datetime import date
from typing import List

from pydantic import BaseModel

from openg2p_fastapi_common.schemas import (
    G2PRequest,
    G2PRequestBody,
    G2PRequestHeader,
    G2PPaginationRequest,
    G2PResponse,
    G2PResponseBody,
    G2PResponseHeader,
    G2PResponseStatus,
    G2PPaginationResponse,
)

class BenefitCode(BaseModel):
    id: int
    benefit_code_mnemonic: str
    benefit_type: str
    benefit_code_description: str
    benefit_code_max_quantity: float
    measurement_unit: str


class BenefitProgram(BaseModel):
    id: int
    program_name: str
    program_mnemonic: str
    program_description: str
    application_id: int
    application_status: str
    enrolment_date: date
    benefit_codes: List[BenefitCode]


class BenefitProgramRequestPayload(BaseModel):
    # Only needed for get_program; others can omit payload
    program_id: str | None = None
    application_url: str | None = None


class BenefitProgramRequestBody(G2PRequestBody):
    g2p_pagination_request: G2PPaginationRequest | None = None
    g2p_request_payload: BenefitProgramRequestPayload | None = None


class BenefitProgramRequest(G2PRequest):
    g2p_request_header: G2PRequestHeader
    g2p_request_body: BenefitProgramRequestBody

class BenefitProgramResponseBody(G2PResponseBody):
    g2p_response_payload: List[BenefitProgram]


class BenefitProgramDetailResponseBody(G2PResponseBody):
    g2p_response_payload: BenefitProgram


class BenefitProgramResponse(G2PResponse):
    g2p_response_body: BenefitProgramResponseBody


class BenefitProgramDetailResponse(G2PResponse):
    g2p_response_body: BenefitProgramDetailResponseBody
