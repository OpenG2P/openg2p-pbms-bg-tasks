import logging

from openg2p_eee_models.errors import EEEException
from openg2p_eee_models.models import BeneficiaryListSummary
from openg2p_eee_models.schemas import (
    EEESummaryRequest,
    EEESummaryResponse,
)
from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..services import EEESummaryService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class EEESummaryController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["PBMS EEE Eligibility Summary"]
        self.eee_summary_service = EEESummaryService.get_component()

        self.router.add_api_route(
            "/beneficiary_list_summary",
            self.get_eee_summary,
            responses={200: {"model": EEESummaryResponse}},
            methods=["POST"],
        )

    async def get_eee_summary(
        self, eee_summary_request: EEESummaryRequest
    ) -> EEESummaryResponse:
        _logger.debug("Eligibility Summary Request: %s", eee_summary_request)

        try:
            beneficiary_list_summary: BeneficiaryListSummary = (
                await self.eee_summary_service.get_eee_summary(
                    eee_summary_request.message
                )
            )
            eee_summary_response: EEESummaryResponse = (
                await self.eee_summary_service.construct_eee_summary_success_response(
                    eee_summary_request, beneficiary_list_summary
                )
            )
            _logger.info("Eligibility summary retrieved successfully")
            return eee_summary_response

        except EEEException as e:
            error_response: EEESummaryResponse = (
                await self.eee_summary_service.construct_eee_summary_error_response(
                    eee_summary_request, e.code
                )
            )
            return error_response
