import logging
from datetime import datetime
from typing import List

import requests
from openg2p_eee_models.models import Disbursement, DisbursementBatch
from openg2p_eee_models.schemas import RegistrantDetails
from openg2p_g2p_bridge_models.schemas import (
    DisbursementPayload,
    DisbursementRequest,
    DisbursementResponse,
)
from openg2p_g2pconnect_common_lib.schemas import RequestHeader
from openg2p_pbms_models.models import G2PDisbursementCycle, StatusEnum
from openg2p_pbms_models.models.program_definiton import G2PProgramDefinition
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from ..helpers import create_jwt_token

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


def create_disbursement(
    disbursement_batch: DisbursementBatch, eee_session, narrative: str
):
    try:
        registrant_details: List[
            RegistrantDetails
        ] = disbursement_batch.registrant_details
        disbursement_payloads = []

        for registrant in registrant_details:
            registrant_detail = RegistrantDetails(**registrant)

            disbursement_payload = DisbursementPayload(
                mis_reference_number=disbursement_batch.pbms_request_id,
                disbursement_envelope_id=disbursement_batch.bridge_envelope_id,
                beneficiary_id=registrant_detail.registrant_id,
                beneficiary_name="Beneficiary Name",
                disbursement_amount=registrant_detail.entitlement_quantity,
                narrative=narrative,
            )
            disbursement_payloads.append(disbursement_payload)

        disbursement_header = RequestHeader(
            version="1.0.0",
            message_id="string",
            message_ts="string",
            action="create_disbursements",
            sender_id=_config.sender_id,
            sender_uri="",
            receiver_id="",
            total_count=len(registrant_details),
            is_msg_encrypted=False,
            meta="string",
        )

        disbursement_request = DisbursementRequest(
            header=disbursement_header, message=disbursement_payloads
        )
        disbursement_request_json = disbursement_request.model_dump(mode="json")
        _logger.debug(f"Disbursement request payload: {disbursement_request_json}")

        disbursement_url = _config.g2p_bridge_disbursement_url
        _logger.debug(f"Disbursement URL: {disbursement_url}")

        jwt_token = create_jwt_token(disbursement_request_json, _config.private_key)

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": jwt_token,
        }
        _logger.info(
            f"Calling disbursement creation endpoint for disbursement batch id {disbursement_batch.id} having {len(registrant_details)} beneficiaries"
        )

        response = requests.post(
            disbursement_url, json=disbursement_request_json, headers=headers
        )
        response.raise_for_status()
        _logger.info(
            f"Response status code for disbursement batch id {disbursement_batch.id}: {response.status_code}"
        )

        disbursement_response = DisbursementResponse.model_validate(response.json())
        _logger.debug(
            f"Response for disbursement batch id {disbursement_batch.id}: {disbursement_response}"
        )

        return disbursement_response, None

    except Exception as e:
        _logger.error(f"Error occurred while calling disbursement API: {e}")
        return None, str(e)


def construct_narrative(disbursement_cycle_mnemonic: str, program_mnemonic: str) -> str:
    return f"{program_mnemonic} - {disbursement_cycle_mnemonic}"


@celery_app.task(name="disbursement_worker")
def disbursement_worker(id: int):
    _logger.info("Starting disbursement batch worker")
    eee_session_maker = sessionmaker(
        bind=_engine.get("db_engine_eee"), expire_on_commit=False
    )
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )

    with pbms_session_maker() as pbms_session, eee_session_maker() as eee_session:
        try:
            disbursement_batch = (
                eee_session.query(DisbursementBatch)
                .filter(DisbursementBatch.id == id)
                .first()
            )
            if not disbursement_batch:
                raise Exception(f"No queue entry found for queue id: {id}")

            disbursement_cycle_mnemonic = (
                pbms_session.query(G2PDisbursementCycle.cycle_mnemonic)
                .filter(
                    G2PDisbursementCycle.id == disbursement_batch.disbursement_cycle_id
                )
                .first()
            )
            disbursement_cycle_mnemonic: str = (
                disbursement_cycle_mnemonic[0] if disbursement_cycle_mnemonic else None
            )

            if not disbursement_cycle_mnemonic:
                raise Exception(
                    f"No disbursement cycle mnemonic found for batch id: {id}"
                )

            program_mnemonic = (
                pbms_session.query(G2PProgramDefinition.program_mnemonic)
                .filter(G2PProgramDefinition.id == disbursement_batch.program_id)
                .first()
            )
            program_mnemonic: str = program_mnemonic[0] if program_mnemonic else None

            if not program_mnemonic:
                raise Exception(f"No program mnemonic found for batch id: {id}")

            narrative: str = construct_narrative(
                disbursement_cycle_mnemonic, program_mnemonic
            )

            # Call the separated disbursement creation function
            disbursement_response, error = create_disbursement(
                disbursement_batch, eee_session, narrative
            )
            if error:
                raise Exception(f"Error creating disbursement: {error}")

            # Save the disbursement response to the database
            for disbursement in disbursement_response.message:
                _logger.debug(
                    f"Disbursement response: {disbursement.model_dump(mode='json')}"
                )

                disbursement_record = Disbursement(
                    bridge_disbursement_id=disbursement.disbursement_id,
                    disbursement_batch_id=disbursement_batch.id,
                    registrant_id=disbursement.beneficiary_id,
                    bridge_downstream_status=StatusEnum.PENDING.value,
                    bridge_downstream_error_code=None,
                    bridge_polling_attempts=0,
                    bridge_polling_latest_timestamp=datetime.now(),
                )
                eee_session.add(disbursement_record)

            # Update the disbursement batch status to SUCCESS
            disbursement_batch.disbursement_status = StatusEnum.COMPLETE.value
            disbursement_batch.bridge_disbursement_error_code = None
            disbursement_batch.bridge_disbursement_status_attempts += 1
            disbursement_batch.bridge_disbursement_status_latest_timestamp = (
                datetime.now()
            )
            eee_session.commit()
            _logger.info(
                f"DisbursementBatch records created successfully for cycle id: {id}"
            )

        except Exception as e:
            _logger.error(f"Error in disbursement batch worker: {e}")
            if disbursement_batch:
                disbursement_batch.disbursement_status = StatusEnum.PENDING.value
                disbursement_batch.bridge_disbursement_error_code = str(e)
                disbursement_batch.bridge_disbursement_status_attempts += 1
                eee_session.commit()
