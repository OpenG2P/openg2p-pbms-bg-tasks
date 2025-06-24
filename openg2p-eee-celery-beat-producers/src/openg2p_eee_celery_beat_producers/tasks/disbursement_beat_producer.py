import logging
from typing import List

from openg2p_eee_models.models import DisbursementBatch
from openg2p_pbms_models.models import StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="disbursement_beat_producer")
def disbursement_beat_producer():
    _logger.info("Checking for pending disbursement batch status requests")
    eee_session_maker = sessionmaker(
        bind=_engine.get("db_engine_eee"), expire_on_commit=False
    )

    with eee_session_maker() as eee_session:
        disbursement_batches: List[DisbursementBatch] = (
            eee_session.execute(
                select(DisbursementBatch)
                .filter(
                    DisbursementBatch.disbursement_status == StatusEnum.PENDING.value
                )
                .limit(_config.batch_size)
            )
            .scalars()
            .all()
        )
        _logger.debug(
            f"Found {len(disbursement_batches)} pending disbursement batch requests"
        )

        for disbursement_batch in disbursement_batches:
            _logger.info(f"Queueing Disbursement Batch ID: {disbursement_batch.id}")

            # Update the status to PROCESSING
            disbursement_batch.disbursement_status = StatusEnum.PROCESSING.value
            _logger.info(
                f"Updating status for Disbursement Batch ID: {disbursement_batch.id} to PROCESSING"
            )
            eee_session.commit()
            worker_type = WorkerTypes.DISBURSEMENT_WORKER
            # Send task to the appropriate celery worker
            celery_app.send_task(
                worker_type,
                args=(disbursement_batch.id,),
                queue=_config.eee_task_worker_queue,
            )
            _logger.info(
                f"Sent task to disbursement_status_worker for Disbursement Batch ID: {disbursement_batch.id}"
            )

    _logger.info("Completed processing pending Disbursement Batch requests")
