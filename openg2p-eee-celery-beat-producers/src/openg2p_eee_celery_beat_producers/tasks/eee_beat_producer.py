import logging

from openg2p_eee_models.models import EnumStatus, G2PQueEligibilityRequest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="eee_beat_producer")
def eee_beat_producer():
    _logger.info("Checking for pending eligibility requests")
    session_maker = sessionmaker(bind=_engine, expire_on_commit=False)

    with session_maker() as session:
        # Fetch rows with PENDING status
        pending_entries = (
            session.execute(
                select(G2PQueEligibilityRequest)
                .filter(G2PQueEligibilityRequest.enumeration_status == EnumStatus.PENDING.value)
                .limit(_config.batch_size)
            )
            .scalars()
            .all()
        )

        for entry in pending_entries:
            _logger.info(f"Queueing eligibility request ID: {entry.id}")

            # Send task to Celery worker
            celery_app.send_task(
                "eligibility_request_worker",
                args=(entry.id,),
                queue="eligibility_request_queue",
            )

    _logger.info("Completed processing pending eligibility requests")
