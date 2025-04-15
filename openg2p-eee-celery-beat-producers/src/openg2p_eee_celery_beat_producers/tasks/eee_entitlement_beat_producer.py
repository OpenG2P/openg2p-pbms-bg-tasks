import logging
from typing import List

from openg2p_eee_models.models import EEEDetails, StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="eee_entitlement_beat_producer")
def eee_entitlement_beat_producer():
    _logger.info("Checking for pending EEE entitlement requests in EEEDetails")
    eee_session_maker = sessionmaker(
        bind=_engine.get("db_engine_eee"), expire_on_commit=False
    )
    with eee_session_maker() as eee_session:
        # Fetch rows with PENDING status
        eee_details: List[EEEDetails] = (
            eee_session.execute(
                select(EEEDetails)
                .filter(
                    (
                        EEEDetails.entitlement_status
                        == StatusEnum.PENDING.value
                    )
                )
                .limit(_config.batch_size)
            )
            .scalars()
            .all()
        )
        _logger.info(
            f"Found {len(eee_details)} pending entitlement requests"
        )

        for eee_detail in eee_details:
            _logger.info(f"Queueing EEE entitlement request ID: {eee_detail.id}")

            eee_detail.entitlement_status = StatusEnum.PROCESSING.value
            eee_session.add(eee_detail)

            _logger.info(
                f"Updating status for {WorkerTypes.ENTITLEMENT_REQUEST_WORKER} to PROCESSING in EEE entitlement request ID: {eee_detail.id}"
            )

            # Send task to appropriate celery worker
            celery_app.send_task(
                WorkerTypes.ENTITLEMENT_REQUEST_WORKER,
                args=(eee_detail.id,),
                queue=_config.eee_task_worker_queue,
            )
            _logger.info(
                f"Sent task to {WorkerTypes.ENTITLEMENT_REQUEST_WORKER} for EEE entitlement request ID: {eee_detail.id}"
            )
        eee_session.commit()

    _logger.info("Completed processing pending EEE entitlement requests")
