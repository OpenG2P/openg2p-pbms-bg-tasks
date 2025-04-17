import logging
from typing import List

from openg2p_pbms_models.models import G2PDisbursementCycle, StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="envelop_batch_beat_producer")
def envelop_batch_beat_producer():
    _logger.info("Checking for pending disbursement requests")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )

    with pbms_session_maker() as pbms_session:
        # Fetch rows with PENDING status for envelope or disbursement processes
        g2p_disbursement_cycles: List[G2PDisbursementCycle] = (
            pbms_session.execute(
                select(G2PDisbursementCycle)
                .filter(
                    (
                        G2PDisbursementCycle.envelope_creation_status
                        == StatusEnum.PENDING.value
                    )
                    | (
                        G2PDisbursementCycle.batch_creation_status
                        == StatusEnum.PENDING.value
                    )
                )
                .limit(_config.batch_size)
            )
            .scalars()
            .all()
        )
        _logger.debug(
            f"Found {len(g2p_disbursement_cycles)} pending cycle requests"
        )

        for g2p_disbursement_cycle in g2p_disbursement_cycles:
            _logger.info(f"Queueing Disbursement Cycle ID: {g2p_disbursement_cycle.id}")

            if (
                g2p_disbursement_cycle.envelope_creation_status
                == StatusEnum.PENDING.value
            ):
                worker_type = WorkerTypes.ENVELOPE_CREATION_REQUEST_WORKER
                g2p_disbursement_cycle.envelope_creation_status = (
                    StatusEnum.PROCESSING.value
                )
            elif (
                g2p_disbursement_cycle.batch_creation_status == StatusEnum.PENDING.value
            ):
                worker_type = WorkerTypes.BATCH_CREATION_REQUEST_WORKER
                g2p_disbursement_cycle.batch_creation_status = (
                    StatusEnum.PROCESSING.value
                )

            _logger.info(
                f"Updating status for {worker_type} to PROCESSING in Disbursement Cycle ID: {g2p_disbursement_cycle.id}"
            )
            pbms_session.commit()

            # Send task to appropriate celery worker
            celery_app.send_task(
                worker_type,
                args=(g2p_disbursement_cycle.id,),
                queue=_config.eee_task_worker_queue,
            )
            _logger.info(
                f"Sent task to {worker_type} for Disbursement Cycle ID: {g2p_disbursement_cycle.id}"
            )

    _logger.info("Completed processing pending Disbursement Cycle requests")
