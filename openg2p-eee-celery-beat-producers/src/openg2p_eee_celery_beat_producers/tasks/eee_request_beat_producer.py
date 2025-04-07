import logging
from typing import List

from openg2p_pbms_models.models import G2PQueEEERequest, StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="eee_request_beat_producer")
def eee_request_beat_producer():
    _logger.info("Checking for pending EEE requests")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    with pbms_session_maker() as pbms_session:
        # Fetch rows with PENDING status
        que_eee_requests: List[G2PQueEEERequest] = (
            pbms_session.execute(
                select(G2PQueEEERequest)
                .filter(
                    (
                        G2PQueEEERequest.eligibility_process_status
                        == StatusEnum.PENDING.value
                    )
                    | (
                        G2PQueEEERequest.entitlement_process_status
                        == StatusEnum.PENDING.value
                    )
                )
                .limit(_config.batch_size)
            )
            .scalars()
            .all()
        )
        _logger.info(
            f"Found {len(que_eee_requests)} pending requests in {StatusEnum.PENDING.value}"
        )

        for que_eee_request in que_eee_requests:
            _logger.info(f"Queueing EEE request ID: {que_eee_request.id}")

            if que_eee_request.eligibility_process_status == StatusEnum.PENDING.value:
                worker_type = WorkerTypes.ELIGIBILITY_REQUEST_WORKER
                que_eee_request.eligibility_process_status = StatusEnum.PROCESSING.value

            elif que_eee_request.entitlement_process_status == StatusEnum.PENDING.value:
                worker_type = WorkerTypes.ENTITLEMENT_REQUEST_WORKER
                que_eee_request.entitlement_process_status = StatusEnum.PROCESSING.value

            _logger.info(
                f"Updating status for {worker_type} to PROCESSING in EEE request ID: {que_eee_request.id}"
            )
            pbms_session.commit()

            # Send task to appropriate celery worker
            celery_app.send_task(
                worker_type,
                args=(que_eee_request.id,),
                queue=_config.eee_task_worker_queue,
            )
            _logger.info(
                f"Sent task to {worker_type} for EEE request ID: {que_eee_request.id}"
            )

    _logger.info("Completed processing pending EEE requests")
