import asyncio
import logging
from datetime import datetime

import requests
from openg2p_eee_registry_adapters.factory import EEERegistryFactory
from openg2p_eee_registry_adapters.interface import EEERegistryInterface
from openg2p_eee_registry_adapters.schema import EEESummaryPayload
from openg2p_g2p_bridge_models.schemas import (
    DisbursementEnvelopePayload,
    DisbursementEnvelopeRequest,
    DisbursementEnvelopeResponse,
)
from openg2p_g2pconnect_common_lib.schemas import RequestHeader
from openg2p_pbms_models.models import (
    G2PDeliveryCodes,
    G2PDisbursementCycle,
    G2PProgramDefinition,
    StatusEnum,
)
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


def create_disbursement_envelope(
    program_definition: G2PProgramDefinition,
    disbursement_cycle: G2PDisbursementCycle,
    eee_summary_payload: EEESummaryPayload,
    pbms_session,
):
    delivery_code: G2PDeliveryCodes = (
        pbms_session.query(G2PDeliveryCodes)
        .filter(
            G2PDeliveryCodes.id == program_definition.delivery_id,
        )
        .first()
    )

    envelope_payload = DisbursementEnvelopePayload(
        benefit_program_mnemonic=program_definition.program_mnemonic,
        cycle_code_mnemonic=disbursement_cycle.cycle_mnemonic,
        number_of_beneficiaries=eee_summary_payload.general_summary.number_of_registrants,
        number_of_disbursements=eee_summary_payload.general_summary.number_of_registrants,
        total_disbursement_amount=eee_summary_payload.general_summary.total_entitlement_amount,
        disbursement_schedule_date=disbursement_cycle.disbursement_schedule_date,
        disbursement_frequency=program_definition.disbursement_frequency.value,
        disbursement_currency_code=delivery_code.measurement_unit,  # TODO Add a separate unit for currency ISO
    )

    # TODO: Refactor later
    disbursement_envelope_request_header = RequestHeader(
        version="1.0.0",
        message_id="string",
        message_ts="string",
        action="string",
        sender_id="string",
        sender_uri="",
        receiver_id="",
        total_count=1,
        is_msg_encrypted=False,
        meta="string"
    )
    disbursement_envelope_request: DisbursementEnvelopeRequest = (
        DisbursementEnvelopeRequest(
            header=disbursement_envelope_request_header,
            message=envelope_payload
        )
    )
    _logger.debug(f"Disbursement Envelope Request: {disbursement_envelope_request.model_dump(mode='json')}")

    envelope_creation_url = _config.g2p_bridge_envelope_creation_url
    _logger.debug(f"Envelope Creation URL: {envelope_creation_url}")

    try:
        response = requests.post(
            envelope_creation_url, json=disbursement_envelope_request.model_dump(mode='json')
        )
        response.raise_for_status()

        envelope_response = DisbursementEnvelopeResponse.model_validate(response.json())
        return envelope_response, None

    except Exception as e:
        _logger.error(f"Error occurred while calling envelope creation API: {e}")
        return None, str(e)

async def fetch_eee_summary(eee_registry_interface, pbms_request_id, eee_session_maker):
    async with eee_session_maker() as eee_session:
        return await eee_registry_interface.get_summary(pbms_request_id, eee_session)


@celery_app.task(name="envelope_creation_request_worker")
def envelope_creation_request_worker(id: int):
    _logger.info("Starting envelope creation request")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    eee_session_maker = async_sessionmaker(
        bind=_engine.get("db_engine_eee_async"), expire_on_commit=False
    )

    with pbms_session_maker() as pbms_session:
        disbursement_cycle = None
        try:
            # Fetch the queue entry from pbms db using id
            disbursement_cycle = (
                pbms_session.query(G2PDisbursementCycle)
                .filter(G2PDisbursementCycle.id == id)
                .first()
            )

            # Get ProgramDefinition using program_id from disbursement_cycle
            program_definition = (
                pbms_session.query(G2PProgramDefinition)
                .filter(G2PProgramDefinition.id == disbursement_cycle.program_id)
                .first()
            )
            if not program_definition:
                raise Exception(
                    f"No program found for program id: {disbursement_cycle.program_id}"
                )

            if not disbursement_cycle:
                raise Exception(f"No queue entry found for queue id: {id}")

            eee_registry_interface: EEERegistryInterface = (
                EEERegistryFactory.get_computation_class(
                    program_definition.target_registry_type,
                )
            )

            _logger.info(
                f"Fetching summary for pbms_request_id: {disbursement_cycle.pbms_request_id}"
            )

            # Fetch the eee summary from eee db using pbms_request_id based on target_registry_type
            eee_summary_payload: EEESummaryPayload = asyncio.run(
                fetch_eee_summary(
                    eee_registry_interface,
                    disbursement_cycle.pbms_request_id,
                    eee_session_maker,
                )
            )


            if not eee_summary_payload:
                raise Exception(
                    f"No summary found for pbms_request_id: {disbursement_cycle.pbms_request_id}"
                )

            # Call the envelope creation service API

            disbursement_envelope_response, error = create_disbursement_envelope(
                program_definition,
                disbursement_cycle,
                eee_summary_payload,
                pbms_session,
            )
            _logger.debug(f"Disbursement envelope response: {disbursement_envelope_response}")

            if error:
                raise Exception(f"Error occurred while creating envelope: {error}")

            disbursement_cycle.bridge_envelope_id = (
                disbursement_envelope_response.message.disbursement_envelope_id
            )
            disbursement_cycle.envelope_creation_attempts += 1
            disbursement_cycle.envelope_creation_latest_error_code = None
            disbursement_cycle.envelope_creation_status = StatusEnum.COMPLETE.value
            disbursement_cycle.envelope_creation_latest_timestamp = datetime.now()
            disbursement_cycle.batch_creation_status = StatusEnum.PENDING.value
            pbms_session.commit()

            _logger.info(f"Envelope creation successful for disbursement cycle id: {id}")

        except Exception as e:
            _logger.error(
                f"Exception occurred while processing envelope creation request: {e}"
            )
            if disbursement_cycle:
                disbursement_cycle.envelope_creation_attempts += 1
                disbursement_cycle.envelope_creation_latest_error_code = str(e)
                disbursement_cycle.envelope_creation_status = StatusEnum.PENDING.value
                disbursement_cycle.envelope_creation_latest_timestamp = datetime.now()
                pbms_session.commit()
