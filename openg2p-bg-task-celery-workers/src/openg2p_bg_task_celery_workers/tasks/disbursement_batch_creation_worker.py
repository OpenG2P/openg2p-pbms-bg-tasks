import logging
from datetime import datetime, timezone
from typing import List

from openg2p_bg_task_models.models import (
    BeneficiaryListDetails,
    DisbursementBatch,
    DisbursementEnvelope,
)
from openg2p_bg_task_models.schemas import Disbursement, RegistrantDetails
from openg2p_pbms_models.models import (
    G2PBeneficiaryList,
    StatusEnum,
)
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="disbursement_batch_creation_worker")
def disbursement_batch_creation_worker(id: int):
    _logger.info(
        f"Starting disbursement batch creation request for benefiicary list id: {id}"
    )

    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    bg_task_session_maker = sessionmaker(
        bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
    )

    with pbms_session_maker() as pbms_session, bg_task_session_maker() as bg_task_session:
        beneficiary_list = None
        try:
            # Fetch the queue entry from pbms db using id
            beneficiary_list = (
                pbms_session.query(G2PBeneficiaryList)
                .filter(G2PBeneficiaryList.id == id)
                .first()
            )

            if not beneficiary_list:
                raise Exception(f"No beneficiary list found for id: {id}")

            # Get all BeneficiaryListDetails rows for the given beneficiary_list_id
            beneficiary_list_details = (
                bg_task_session.query(BeneficiaryListDetails)
                .filter(
                    BeneficiaryListDetails.beneficiary_list_id
                    == beneficiary_list.beneficiary_list_id
                )
                .all()
            )
            # Get all DisbursementEnvelope rows for the given beneficiary_list_id
            disbursement_envelopes = (
                bg_task_session.query(DisbursementEnvelope)
                .filter(
                    DisbursementEnvelope.beneficiary_list_id
                    == beneficiary_list.beneficiary_list_id
                )
                .all()
            )

            _logger.info(
                f"Total detail batches fetched from BeneficiaryListDetails: {len(beneficiary_list_details)}"
            )
            _logger.info(
                f"Total disbursement envelopes fetched from BeneficiaryListDetails: {len(disbursement_envelopes)}"
            )

            # Iterate over disbursement envelopes and beneficiary list details to create disbursement batches
            disbursement_batches_by_envelope_by_batch: List[DisbursementBatch] = []
            for disbursement_envelope in disbursement_envelopes:
                for beneficiary_list_detail in beneficiary_list_details:
                    disbursements_by_benefit_code: List[Disbursement] = []
                    for registrant_detail in beneficiary_list_detail.registrant_details:
                        registrant_detail = RegistrantDetails(**registrant_detail)
                        disbursement_by_benefit_code = Disbursement(
                            beneficiary_id=registrant_detail.registrant_id,
                            entitlement=registrant_detail.entitlement[
                                disbursement_envelope.benefit_code_id
                            ],
                        )
                        disbursements_by_benefit_code.append(
                            disbursement_by_benefit_code.model_dump(mode="json")
                        )

                    disbursement_batch_by_envelope = DisbursementBatch(
                        disbursements=disbursements_by_benefit_code,
                        disbursement_envelope_id=disbursement_envelope.id,
                        disbursement_cycle_id=disbursement_envelope.disbursement_cycle_id,
                        beneficiary_list_details_id=beneficiary_list_detail.id,
                        beneficiary_list_id=beneficiary_list.beneficiary_list_id,
                    )
                    disbursement_batches_by_envelope_by_batch.append(
                        disbursement_batch_by_envelope
                    )

            _logger.info(
                f"disbursement batches: {disbursement_batches_by_envelope_by_batch}"
            )

            # Bulk insert all the disbursement batches
            bg_task_session.add_all(disbursement_batches_by_envelope_by_batch)

            _logger.info(
                f"Disbursement batch records created successfully for beneficiary list id: {id}"
            )

            beneficiary_list.disbursement_batch_creation_status = (
                StatusEnum.COMPLETE.value
            )
            beneficiary_list.dbc_number_of_attempts += 1
            beneficiary_list.dbc_processed_date = datetime.now(timezone.utc)
            _logger.info(
                f"Compelted processing disbursement batch creation for beneficiary list id: {id}"
            )
            bg_task_session.commit()
            pbms_session.commit()

        except Exception as e:
            _logger.error(f"Error in batch creation request worker: {e}")

            pbms_session.rollback()
            bg_task_session.rollback()

            if beneficiary_list:
                beneficiary_list.dbc_number_of_attempts += 1
                beneficiary_list.disbursement_batch_creation_status = (
                    StatusEnum.PENDING.value
                    if beneficiary_list.dbc_number_of_attempts
                    < _config.worker_max_attempts
                    else StatusEnum.FAILED.value
                )
                beneficiary_list.dbc_latest_error_code = str(e)
                pbms_session.commit()
