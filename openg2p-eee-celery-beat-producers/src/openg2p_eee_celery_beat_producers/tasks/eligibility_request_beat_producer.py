import logging

from openg2p_eee_models.models import EnumStatus, G2PQueEligibilityRequest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="eligibility_request_beat_producer")
def eligibility_request_beat_producer():
    _logger.info("Checking for pending eligibility requests")
    session_maker = sessionmaker(bind=_engine, expire_on_commit=False)

    with session_maker() as session:
        # Fetch rows with PENDING status
        pending_eligibility_requests = (
            session.execute(
                select(G2PQueEligibilityRequest)
                .filter(
                    G2PQueEligibilityRequest.enumeration_status
                    == EnumStatus.PENDING.value
                )
                .limit(_config.batch_size)
            )
            .scalars()
            .all()
        )
        _logger.debug(f"Found {len(pending_eligibility_requests)} pending requests")

        for request in pending_eligibility_requests:
            _logger.info(f"Queueing eligibility request ID: {request.id}")

            # Send task to Celery worker
            celery_app.send_task(
                _config.eligibility_request_worker,
                args=(request.id,),
                queue=_config.eligibility_request_queue,
            )

    _logger.info("Completed processing pending eligibility requests")
