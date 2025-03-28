import logging
from datetime import datetime
from typing import List
import requests

from openg2p_eee_models.models import EEESummary
from openg2p_eee_registry_adapters.factory import EEERegistryFactory
from openg2p_eee_registry_adapters.interface import EEERegistryInterface
from openg2p_eee_registry_adapters.schema import EEESummaryPayload
from openg2p_pbms_models.models import (
    StatusEnum,
    G2PDisbursementCycle,
    G2PProgramDefinition,
)
from openg2p_g2p_bridge_models.schemas import DisbursementEnvelopePayload, DisbursementEnvelopeRequest, DisbursementEnvelopeResponse
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="envelope_creation_request_worker")
def envelope_creation_request_worker(id: int):
    _logger.info("Starting envelope creation request")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    eee_session_maker = sessionmaker(
        bind=_engine.get("db_engine_eee"), expire_on_commit=False
    )

    with pbms_session_maker() as pbms_session, eee_session_maker() as eee_session:
        g2p_disbursement_cycle = None
        try:
            # Fetch the queue entry from pbms db using id
            g2p_disbursement_cycle = (
                pbms_session.query(G2PDisbursementCycle)
                .filter(G2PDisbursementCycle.id == id)
                .first()
            )

            if not g2p_disbursement_cycle:
                raise Exception(f"No queue entry found for queue id: {id}")
            
            eee_registry_interface: EEERegistryInterface = (
                    EEERegistryFactory.get_computation_class(g2p_disbursement_cycle.target_registry_type)
                )

            # Fetch the eee summary from eee db using pbms_request_id based on target_registry_type
            eee_summary_payload: EEESummaryPayload = eee_registry_interface.get_eee_summary(
                eee_session,
                g2p_disbursement_cycle.pbms_request_id,
            )

            if not eee_summary_payload:
                raise Exception(f"No summary found for pbms_request_id: {g2p_disbursement_cycle.pbms_request_id}")

            # Call the envelope creation service API
            
            disbursement_envelope_response, error = create_disbursement_envelope(
                g2p_disbursement_cycle.program,
                g2p_disbursement_cycle.cycle_mnemonic,
                eee_summary_payload,
            )

            if error:
                raise Exception(f"Error occurred while creating envelope: {error}")

            g2p_disbursement_cycle.bridge_envelope_id = disbursement_envelope_response.message.disbursement_envelope_id
            g2p_disbursement_cycle.envelope_creation_attempts += 1
            g2p_disbursement_cycle.envelope_creation_latest_error_code = None
            g2p_disbursement_cycle.envelope_creation_status = StatusEnum.SUCCESS.value
            g2p_disbursement_cycle.envelope_creation_latest_timestamp = datetime.now()
            g2p_disbursement_cycle.batch_creation_status = StatusEnum.PENDING.value
            pbms_session.commit()

        except Exception as e:
            _logger.error(f"Exception occurred while processing envelope creation request: {e}")
            if g2p_disbursement_cycle:
                g2p_disbursement_cycle.envelope_creation_attempts += 1
                g2p_disbursement_cycle.envelope_creation_latest_error_code = str(e)
                g2p_disbursement_cycle.envelope_creation_status = StatusEnum.FAILED.value
                g2p_disbursement_cycle.envelope_creation_latest_timestamp = datetime.now()
                pbms_session.commit()

    
def create_disbursement_envelope(g2p_program_definition: G2PProgramDefinition, cycle_mnemonic: str, eee_summary_payload: EEESummaryPayload):

    envelope_payload = DisbursementEnvelopePayload(
        benefit_program_mnemonic=g2p_program_definition.program_mnemonic,
        cycle_code_mnemonic=cycle_mnemonic,
        number_of_beneficiaries=eee_summary_payload.general_summary.number_of_registrants,
        total_disbursement_amount=eee_summary_payload.general_summary.total_entitlement_amount,
        disbursement_schedule_date=eee_summary_payload.general_summary.disbursement_schedule_date,
        disbursement_frequency=g2p_program_definition.disbursement_frequency,
    )
    
    disbursement_envelope_request_body: DisbursementEnvelopeRequest = DisbursementEnvelopeRequest(message=envelope_payload)
    
    envelope_creation_url = _config.g2p_bridge_envelope_creation_url

    try:
        response = requests.post(envelope_creation_url, json=disbursement_envelope_request_body.model_dump_json())
        response.raise_for_status()
        
        envelope_response = DisbursementEnvelopeResponse.model_validate(response.json())
        return envelope_response, None

    except Exception as e:
        _logger.error(f"Error occurred while calling envelope creation API: {e}")
        return None, str(e)