import logging

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
            disbursement_batches = []
            for disbursement_envelope in disbursement_envelopes:
                for beneficiary_list_detail in beneficiary_list_details:
                    disbursements = []
                    for registrant_detail in beneficiary_list_detail.registrant_details:
                        registrant_detail = RegistrantDetails(**registrant_detail)
                        disbursement = Disbursement(
                            beneficiary_id=registrant_detail.registrant_id,
                            entitlement=registrant_detail.entitlement[
                                disbursement_envelope.benefit_code_id
                            ],
                        )
                        disbursements.append(disbursement.model_dump(mode="json"))
                        print(disbursements)

                    disbursement_batch = DisbursementBatch(
                        disbursements=disbursements,
                        disbursement_envelope_id=disbursement_envelope.disbursement_envelope_id,
                        disbursement_cycle_id=disbursement_envelope.disbursement_cycle_id,
                        beneficiary_list_details_id=beneficiary_list_detail.id,
                        beneficiary_list_id=beneficiary_list.beneficiary_list_id,
                    )
                    disbursement_batches.append(disbursement_batch)

            _logger.info(f"disbursement batches: {disbursement_batches}")

            # Bulk insert all the disbursement batches
            bg_task_session.add_all(disbursement_batches)

            # Commit the changes to the database
            bg_task_session.commit()
            _logger.info(
                f"Disbursement batch records created successfully for beneficiary list id: {id}"
            )

            beneficiary_list.disbursement_batch_creation_status = (
                StatusEnum.COMPLETE.value
            )
            _logger.info(
                f"Compelted processing disbursement batch creation for beneficiary list id: {id}"
            )
            pbms_session.commit()

        except Exception as e:
            _logger.error(f"Error in batch creation request worker: {e}")

            if beneficiary_list:
                beneficiary_list.disbursement_batch_creation_status = (
                    StatusEnum.PENDING.value
                )
                pbms_session.commit()
