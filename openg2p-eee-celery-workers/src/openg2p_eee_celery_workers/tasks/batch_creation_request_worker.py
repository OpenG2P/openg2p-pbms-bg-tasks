import logging
from datetime import datetime
from typing import List

from openg2p_eee_models.models import DisbursementBatch, EEEDetails
from openg2p_pbms_models.models import (
    G2PDisbursementCycle,
    StatusEnum,
)
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="batch_creation_request_worker")
def batch_creation_request_worker(id: int):
    _logger.info("Starting batch creation request")
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

            # Get registrants
            registrant_ids = eee_session.execute(
                select(EEEDetails.registrant_id).where(
                    EEEDetails.pbms_request_id == g2p_disbursement_cycle.pbms_request_id
                )
            )
            registrant_ids: List[str] = registrant_ids.scalars().all()

            disbursement_batch_size = _config.disbursement_batch_size

            # Divide registrant_ids into batches
            batches = [
                registrant_ids[i : i + disbursement_batch_size]
                for i in range(0, len(registrant_ids), disbursement_batch_size)
            ]
            _logger.info(f"Total batches created: {len(batches)}")

            for batch in batches:
                # Create DisbursementBatch records
                disbursement_batch = DisbursementBatch(
                    disbursement_cycle_id=g2p_disbursement_cycle.id,
                    program_id=g2p_disbursement_cycle.program_id,
                    bridge_envelope_id=g2p_disbursement_cycle.bridge_envelope_id,
                    pbms_request_id=g2p_disbursement_cycle.pbms_request_id,
                    registrant_ids=batch,
                    disbursement_status=StatusEnum.PENDING.value,
                )
                eee_session.add(disbursement_batch)

            # Commit the changes to the database
            eee_session.commit()
            _logger.info(f"DisbursementBatch records created successfully for cycle id: {id}")

            g2p_disbursement_cycle.batch_creation_status = StatusEnum.COMPLETE.value
            g2p_disbursement_cycle.batch_creation_latest_error_code = None
            g2p_disbursement_cycle.batch_creation_attempts += 1
            g2p_disbursement_cycle.batch_creation_latest_timestamp = datetime.now()
            pbms_session.commit()

        except Exception as e:
            _logger.error(f"Error in batch creation request worker: {e}")
            if g2p_disbursement_cycle:
                g2p_disbursement_cycle.batch_creation_latest_error_code = str(e)
                g2p_disbursement_cycle.batch_creation_attempts += 1
                pbms_session.commit()
