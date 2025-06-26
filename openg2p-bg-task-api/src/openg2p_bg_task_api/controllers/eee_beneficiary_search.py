import logging

from openg2p_bg_task_models.errors import EEEException
from openg2p_bg_task_models.schemas import (
    EEEBeneficiarySearchRequest,
    EEEBeneficiarySearchResponse,
    EEEBeneficiarySearchResponsePayload,
)
from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..services import EEEBeneficiarySearchService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class EEEBeneficiarySearchController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["PBMS EEE Beneficiary Search"]
        self.eee_beneficiary_search_service = (
            EEEBeneficiarySearchService.get_component()
        )

        self.router.add_api_route(
            "/search_beneficiaries",
            self.search_beneficiaries,
            responses={200: {"model": EEEBeneficiarySearchResponse}},
            methods=["POST"],
        )

    async def search_beneficiaries(
        self, eee_beneficiary_search_request: EEEBeneficiarySearchRequest
    ) -> EEEBeneficiarySearchResponse:
        _logger.debug("Beneficiary Search Request: %s", eee_beneficiary_search_request)

        try:
            eee_beneficiary_search_response_payload: EEEBeneficiarySearchResponsePayload = await self.eee_beneficiary_search_service.search_beneficiaries(
                eee_beneficiary_search_request.message
            )
            eee_beneficiary_search_response: EEEBeneficiarySearchResponse = await self.eee_beneficiary_search_service.construct_beneficiary_search_success_response(
                eee_beneficiary_search_request, eee_beneficiary_search_response_payload
            )
            _logger.info("Beneficiaries retrieved successfully")
            _logger.info(
                "Beneficiary Search Response: %s", eee_beneficiary_search_response
            )
            return eee_beneficiary_search_response

        except EEEException as e:
            error_response: EEEBeneficiarySearchResponse = await self.eee_beneficiary_search_service.construct_beneficiary_search_error_response(
                eee_beneficiary_search_request, e.code
            )
            return error_response
