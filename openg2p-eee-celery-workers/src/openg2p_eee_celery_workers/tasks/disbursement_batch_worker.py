import logging
from datetime import datetime, timezone

import requests
from openg2p_eee_models.models import Disbursement, DisbursementBatch, EEEDetails
from openg2p_g2p_bridge_models.schemas import (
    DisbursementPayload,
    DisbursementRequest,
    DisbursementResponse,
)
from openg2p_pbms_models.models import StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


def create_disbursement(disbursement_batch: DisbursementBatch, eee_session):
    try:
        registrant_ids = disbursement_batch.registrant_ids
        disbursement_payloads = []

        for registrant_id in registrant_ids:
            result = eee_session.execute(
                select(EEEDetails).where(
                    EEEDetails.registrant_id == registrant_id,
                    EEEDetails.pbms_request_id == disbursement_batch.pbms_request_id
                )
            ).first()
            if not result:
                raise Exception(f"No registrant details found for id: {registrant_id}")

            registrant_details = result[0]
            payload = DisbursementPayload(
                mis_reference_number=disbursement_batch.pbms_request_id,
                disbursement_id=None,
                disbursement_envelope_id=disbursement_batch.bridge_envelope_id,
                beneficiary_id=registrant_id,
                beneficiary_name=None,
                disbursement_amount=registrant_details.quantity,
                narrative=None,
                receipt_time_stamp=datetime.utcnow(),
                cancellation_status=None,
                cancellation_time_stamp=None,
                response_error_codes=None
            )
            disbursement_payloads.append(payload)

        disbursement_request = DisbursementRequest(message=disbursement_payloads)
        _logger.info(f"Disbursement request payload: {disbursement_request}")

        disbursement_url = _config.g2p_bridge_disbursement_url
        _logger.info(f"Disbursement URL: {disbursement_url}")

        response = requests.post(disbursement_url, json=disbursement_request.model_dump_json())
        response.raise_for_status()
        disbursement_response = DisbursementResponse.model_validate(response.json())
        return disbursement_response, None

    except Exception as e:
        _logger.error(f"Error occurred while calling disbursement API: {e}")
        return None, str(e)


@celery_app.task(name="disbursement_batch_worker")
def disbursement_batch_worker(id: int):
    _logger.info("Starting disbursement batch worker")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    eee_session_maker = sessionmaker(
        bind=_engine.get("db_engine_eee"), expire_on_commit=False
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

            # Call the separated disbursement creation function
            disbursement_response, error = create_disbursement(disbursement_batch, eee_session)
            if error:
                raise Exception(f"Error creating disbursement: {error}")

            # Save the disbursement response to the database
            for disb in disbursement_response.message:
                disbursement_record = Disbursement(
                    disbursement_id=disb.disbursement_id,
                    disbursement_batch_id=disbursement_batch.id,
                    registrant_id=disb.beneficiary_id,
                    bridge_disbursement_status=StatusEnum.PENDING.value,
                    bridge_disbursement_status_error_code=None,
                    bridge_disbursement_status_attempts=0,
                    bridge_disbursement_status_latest_timestamp=datetime.now(timezone.utc),
                )
                eee_session.add(disbursement_record)
            
            # Update the disbursement batch status to SUCCESS
            disbursement_batch.disbursement_status = StatusEnum.SUCCESS.value
            disbursement_batch.disbursement_latest_error_code = None
            disbursement_batch.disbursement_attempts += 1
            disbursement_batch.disbursement_timestamp = datetime.now(timezone.utc)
            eee_session.commit()
            _logger.info("DisbursementBatch records created successfully")

        except Exception as e:
            _logger.error(f"Error in disbursement batch worker: {e}")
            if disbursement_batch:
                disbursement_batch.disbursement_status = StatusEnum.FAILED.value
                disbursement_batch.disbursement_latest_error_code = str(e)
                disbursement_batch.disbursement_attempts += 1
                eee_session.commit()
