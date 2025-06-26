import json
import logging

from openg2p_bg_task_models.models import DisbursementBatch
from openg2p_pbms_models.models import (
    G2PBeneficiaryList,
    G2PDisbursementCycle,
    G2PProgramDefinition,
    StatusEnum,
)
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from ..helpers import G2PBridgeDisbursementHelper, create_jwt_token

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


def construct_narrative(disbursement_cycle_mnemonic: str, program_mnemonic: str) -> str:
    return f"{program_mnemonic} - {disbursement_cycle_mnemonic}"


@celery_app.task(name="disbursement_worker")
def disbursement_worker(id: int):
    _logger.info("Starting disbursement batch worker")
    eee_session_maker = sessionmaker(
        bind=_engine.get("db_engine_eee"), expire_on_commit=False
    )
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )

    with pbms_session_maker() as pbms_session, eee_session_maker() as eee_session:
        disbursement_batch = None
        try:
            disbursement_batch = (
                eee_session.query(DisbursementBatch)
                .filter(DisbursementBatch.id == id)
                .first()
            )
            if not disbursement_batch:
                raise Exception(f"No disbursement batch entry found for id: {id}")

            beneficiary_list = (
                pbms_session.query(G2PBeneficiaryList)
                .filter(G2PBeneficiaryList.id == disbursement_batch.beneficiary_list_id)
                .first()
            )

            disbursement_cycle_mnemonic = (
                pbms_session.query(G2PDisbursementCycle.cycle_mnemonic)
                .filter(
                    G2PDisbursementCycle.id == disbursement_batch.disbursement_cycle_id
                )
                .first()
            )
            disbursement_cycle_mnemonic: str = (
                disbursement_cycle_mnemonic[0] if disbursement_cycle_mnemonic else None
            )

            if not disbursement_cycle_mnemonic:
                raise Exception(
                    f"No disbursement cycle mnemonic found for batch id: {id}"
                )

            program_mnemonic = (
                pbms_session.query(G2PProgramDefinition.program_mnemonic)
                .filter(G2PProgramDefinition.id == beneficiary_list.program_id)
                .first()
            )
            program_mnemonic: str = program_mnemonic[0] if program_mnemonic else None

            if not program_mnemonic:
                raise Exception(f"No program mnemonic found for batch id: {id}")

            narrative: str = construct_narrative(
                disbursement_cycle_mnemonic, program_mnemonic
            )

            bridge_disbursement_helper = G2PBridgeDisbursementHelper(
                _config, _logger, create_jwt_token
            )
            (
                disbursement_response,
                error,
            ) = bridge_disbursement_helper.create_disbursement(
                disbursement_batch, eee_session, narrative
            )
            if error:
                raise Exception(f"Error creating disbursement: {error}")

            if isinstance(disbursement_batch.disbursements, str):
                disbursements = json.loads(disbursement_batch.disbursements)
            else:
                disbursements = disbursement_batch.disbursements

            for disbursement_response_message in disbursement_response.message:
                _logger.debug(
                    f"Disbursement response: {disbursement_response_message.model_dump(mode='json')}"
                )
                for disbursement in disbursements:
                    if (
                        disbursement.get("beneficiary_id")
                        == disbursement_response_message.beneficiary_id
                    ):
                        disbursement[
                            "disbursement_id"
                        ] = disbursement_response_message.disbursement_id
                        break
                else:
                    _logger.warning(
                        f"No matching disbursement found in batch {disbursement_batch.id} for beneficiary_id {disbursement_response_message.beneficiary_id}"
                    )
            disbursement_batch.disbursements = json.dumps(disbursements)

            # Update the disbursement batch status
            disbursement_batch.disbursement_status = StatusEnum.COMPLETE.value
            eee_session.commit()
            _logger.info(
                f"Disbursements created successfully for disbursement batch id: {id}"
            )

        except Exception as e:
            _logger.error(f"Error in disbursement batch worker: {e}")

            if disbursement_batch:
                disbursement_batch.disbursement_status = StatusEnum.PENDING.value
                eee_session.commit()
