import logging
from datetime import datetime

from openg2p_eee_models.errors import EEEErrorCodes, EEEException
from openg2p_eee_models.models import BeneficiaryListSummary
from openg2p_eee_models.schemas import (
    EEESummaryRequest,
    EEESummaryRequestPayload,
    EEESummaryResponse,
)
from openg2p_eee_registry_adapters.factory import EEERegistryFactory
from openg2p_eee_registry_adapters.interface import EEERegistryInterface
from openg2p_fastapi_common.service import BaseService
from openg2p_g2pconnect_common_lib.schemas import (
    StatusEnum,
    SyncResponseHeader,
)
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings
from ..engine import get_engine

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


class EEESummaryService(BaseService):
    async def get_eee_summary(
        self, eee_summary_request_payload: EEESummaryRequestPayload
    ) -> BeneficiaryListSummary:
        session_maker = async_sessionmaker(
            bind=_engine.get("db_engine_eee"), expire_on_commit=False
        )
        async with session_maker() as session:
            try:
                summary_computation_interface: EEERegistryInterface = (
                    EEERegistryFactory.get_registry_class(
                        eee_summary_request_payload.target_registry_type
                    )
                )
                beneficiary_list_summary: BeneficiaryListSummary = (
                    await summary_computation_interface.get_summary(
                        eee_summary_request_payload.beneficiary_list_id,
                        session,
                        formated=True,
                    )
                )
                return beneficiary_list_summary

            except Exception as e:
                _logger.error(f"Error fetching eligibility summary : {e}")
                raise EEEException(
                    message="Eligibility request invalid",
                    code=EEEErrorCodes.INVALID_REQUEST,
                ) from e

    async def construct_eee_summary_success_response(
        self,
        eee_summary_request: EEESummaryRequest,
        beneficiary_list_summary: BeneficiaryListSummary,
    ) -> EEESummaryResponse:
        response = EEESummaryResponse(
            header=SyncResponseHeader(
                message_id=eee_summary_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=eee_summary_request.header.action,
                status=StatusEnum.succ,
            ),
            message=beneficiary_list_summary,
        )
        return response

    async def construct_eee_summary_error_response(
        self, eee_summary_request: EEESummaryRequest, error_code: str
    ) -> EEESummaryResponse:
        response = EEESummaryResponse(
            header=SyncResponseHeader(
                message_id=eee_summary_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=eee_summary_request.header.action,
                status=StatusEnum.rjct,
                status_reason_message=error_code,
            ),
            message={},
        )

        return response
