import logging
from typing import List

from openg2p_eee_models.models import BeneficiaryListDetails
from openg2p_pbms_models.models import G2PBeneficiaryList, ListStageEnum, StatusEnum
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from .worker_types import WorkerTypes

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="entitlement_beat_producer")
def entitlement_beat_producer():
    _logger.info("Checking for pending EEE entitlement requests in BeneficiaryListDetails")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    eee_session_maker = sessionmaker(
        bind=_engine.get("db_engine_eee"), expire_on_commit=False
    )
    with eee_session_maker() as eee_session, pbms_session_maker() as pbms_session:
        # # Fetch beneficiary_list with PENDING entitlement status
        # beneficiary_list: G2PBeneficiaryList = (
        #     pbms_session.execute(
        #         select(G2PBeneficiaryList)
        #         .filter(
        #             G2PBeneficiaryList.eligibility_process_status == StatusEnum.COMPLETE.value,
        #             G2PBeneficiaryList.entitlement_process_status == StatusEnum.PENDING.value,
        #             G2PBeneficiaryList.list_stage == ListStageEnum.DISBURSEMENT.value
        #         )
        #     )
        # )
        # Fetch corresponding beneficiary_list_details
        beneficiary_list_details: List[BeneficiaryListDetails] = (
            eee_session.execute(
                select(BeneficiaryListDetails)
                .filter(
                    # BeneficiaryListDetails.beneficiary_list_id == beneficiary_list.beneficiary_list_id,
                    BeneficiaryListDetails.entitlement_status == StatusEnum.PENDING.value
                )
                .limit(_config.batch_size)
            )
            .scalars()
            .all()
        )
        _logger.info(f"Found {len(beneficiary_list_details)} pending entitlement requests")

        for beneficiary_list_detail in beneficiary_list_details:
            _logger.info(f"Queueing EEE entitlement request ID: {beneficiary_list_detail.id}")

            beneficiary_list_detail.entitlement_status = StatusEnum.PROCESSING.value
            eee_session.add(beneficiary_list_detail)

            _logger.info(
                f"Updating status for {WorkerTypes.ENTITLEMENT_WORKER} to PROCESSING in EEE entitlement request ID: {beneficiary_list_detail.id}"
            )

            # Send task to appropriate celery worker
            celery_app.send_task(
                WorkerTypes.ENTITLEMENT_WORKER,
                args=(beneficiary_list_detail.id,),
                queue=_config.eee_task_worker_queue,
            )
            _logger.info(
                f"Sent task to {WorkerTypes.ENTITLEMENT_WORKER} for EEE entitlement request ID: {beneficiary_list_detail.id}"
            )
        eee_session.commit()

    _logger.info("Completed processing pending EEE entitlement requests")
