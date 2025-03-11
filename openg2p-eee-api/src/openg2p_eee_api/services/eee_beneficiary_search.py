import logging
from datetime import datetime

from openg2p_eee_models.schemas import (
    EEEBeneficiarySearchRequest,
    EEEBeneficiarySearchRequestPayload,
    EEEBeneficiarySearchResponse,
    EEEBeneficiarySearchResponsePayload,
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


class EEEBeneficiarySearchService(BaseService):
    async def search_beneficiaries(
        self, eee_beneficiary_search_request_payload: EEEBeneficiarySearchRequestPayload
    ) -> EEEBeneficiarySearchResponsePayload:
        eee_session_maker = async_sessionmaker(
            bind=_engine.get("db_engine_eee"), expire_on_commit=False
        )
        sr_session_maker = async_sessionmaker(
            bind=_engine.get("db_engine_sr"), expire_on_commit=False
        )

        async with eee_session_maker() as eee_session, sr_session_maker() as sr_session:
            try:
                eee_registry_interface: EEERegistryInterface = (
                    EEERegistryFactory.get_summary_computation_class(
                        eee_beneficiary_search_request_payload.target_registry_type
                    )
                )
                eee_beneficiary_search_response_payload: EEEBeneficiarySearchResponsePayload = await eee_registry_interface.search_beneficiaries(
                    eee_session,
                    sr_session,
                    eee_beneficiary_search_request_payload.eee_request_id,
                    eee_beneficiary_search_request_payload.target_registry_type,
                    eee_beneficiary_search_request_payload.search_query,
                    eee_beneficiary_search_request_payload.page,
                    eee_beneficiary_search_request_payload.page_size,
                    eee_beneficiary_search_request_payload.order_by,
                )
                return eee_beneficiary_search_response_payload

            except Exception as e:
                _logger.error(f"Error fetching eligibility summary : {e}")
                raise e

    async def construct_beneficiary_search_success_response(
        self,
        eee_beneficiary_search_request: EEEBeneficiarySearchRequest,
        eee_beneficiary_search_response_payload: EEEBeneficiarySearchResponsePayload,
    ) -> EEEBeneficiarySearchResponse:
        response = EEEBeneficiarySearchResponse(
            header=SyncResponseHeader(
                message_id=eee_beneficiary_search_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=eee_beneficiary_search_request.header.action,
                status=StatusEnum.succ,
            ),
            message=eee_beneficiary_search_response_payload,
        )
        return response

    async def construct_beneficiary_search_error_response(
        self,
        eee_beneficiary_search_request: EEEBeneficiarySearchRequest,
        error_code: str,
    ) -> EEEBeneficiarySearchResponse:
        response = EEEBeneficiarySearchResponse(
            header=SyncResponseHeader(
                message_id=eee_beneficiary_search_request.header.message_id,
                message_ts=datetime.now().isoformat(),
                action=eee_beneficiary_search_request.header.action,
                status=StatusEnum.rjct,
                status_reason_message=error_code,
            ),
            message={},
        )

        return response
