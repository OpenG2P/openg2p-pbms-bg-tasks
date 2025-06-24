import logging
from typing import List

from openg2p_eee_registry_adapters.factory import EEERegistryFactory
from openg2p_eee_registry_adapters.interface import EEERegistryInterface
from openg2p_eee_registry_adapters.schema import EEESummaryPayload
from openg2p_g2p_bridge_models.schemas import (
    DisbursementEnvelopePayload,
)
from openg2p_pbms_models.models import (
    G2PBenefitCodes,
    G2PBeneficiaryList,
    G2PDisbursementCycle,
    G2PProgramDefinition,
    StatusEnum,
)
from openg2p_eee_models.models import DisbursementEnvelope
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from ..helpers.g2p_bridge_helper import G2PBridgeDisbursementHelper
from ..helpers import create_jwt_token

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()

def create_disbursement_envelope_payload(
    benefit_code_id: int,
    total_disbursed_quantity: float,
    program_definition: G2PProgramDefinition,
    disbursement_cycle: G2PDisbursementCycle,
    eee_summary_payload: EEESummaryPayload,
    pbms_session,
) -> DisbursementEnvelopePayload:
    benefit_code: G2PBenefitCodes = (
        pbms_session.query(G2PBenefitCodes)
        .filter(
            G2PBenefitCodes.id == benefit_code_id,
        )
        .first()
    )
    disbursement_envelope_payload = DisbursementEnvelopePayload(
        benefit_program_mnemonic=program_definition.program_mnemonic,
        cycle_code_mnemonic=disbursement_cycle.cycle_mnemonic,
        benefit_code_id=str(benefit_code_id),
        benefit_code_mnemonic=benefit_code.benefit_mnemonic,
        benefit_type=benefit_code.benefit_type,
        cash_distribution_mode=None, # TODO: add to pbmsdb table
        disbursement_cycle_id=str(disbursement_cycle.id),
        number_of_beneficiaries=eee_summary_payload.general_summary.number_of_registrants,
        number_of_disbursements=eee_summary_payload.general_summary.number_of_registrants,
        total_disbursed_quantity=total_disbursed_quantity,
        disbursement_schedule_date=disbursement_cycle.disbursement_schedule_date,
        disbursement_frequency=program_definition.disbursement_frequency.value,
        measurement_unit=benefit_code.measurement_unit,
    )
    return disbursement_envelope_payload


@celery_app.task(name="disbursement_envelope_creation_worker")
def disbursement_envelope_creation_worker(id: int):
    _logger.info(f"Starting disbursement envelope creation request for beneficiary list id: {id}")
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )
    eee_session_maker = sessionmaker(
        bind=_engine.get("db_engine_eee"), expire_on_commit=False
    )

    with pbms_session_maker() as pbms_session, eee_session_maker() as eee_session:
        beneficiary_list = None
        try:
            beneficiary_list = (
                pbms_session.query(G2PBeneficiaryList)
                .filter(G2PBeneficiaryList.id == id)
                .first()
            )

            program_definition: G2PProgramDefinition = (
                pbms_session.query(G2PProgramDefinition)
                .filter(G2PProgramDefinition.id == beneficiary_list.program_id)
                .first()
            )
            
            disbursement_cycle: G2PDisbursementCycle = (
                pbms_session.query(G2PDisbursementCycle)
                .filter(G2PDisbursementCycle.id == beneficiary_list.disbursement_cycle_id)
                .first()
            )

            eee_registry_interface: EEERegistryInterface = (
                EEERegistryFactory.get_registry_class(
                    program_definition.target_registry_type,
                )
            )

            _logger.info(
                f"Fetching summary for beneficiary_list_id: {beneficiary_list.beneficiary_list_id}"
            )

            eee_summary_payload: EEESummaryPayload = (
                eee_registry_interface.get_summary_sync(
                    beneficiary_list.beneficiary_list_id, eee_session
                )
            )

            if not eee_summary_payload:
                raise Exception(
                    f"No summary found for beneficiary_list_id: {beneficiary_list.beneficiary_list_id}"
                )
            
            disbursement_envelope_request_message = []
            for benefit_code_id, total_disbursed_quantity in eee_summary_payload.general_summary.total_entitlement_amount.items():
                disbursement_envelope_payload = create_disbursement_envelope_payload(
                    int(benefit_code_id),
                    total_disbursed_quantity,
                    program_definition,
                    disbursement_cycle,
                    eee_summary_payload,
                    pbms_session
                )
                disbursement_envelope_request_message.append(disbursement_envelope_payload)
            
            # Use the helper class for envelope creation
            bridge_disbursement_helper = G2PBridgeDisbursementHelper(_config, _logger, create_jwt_token)
            disbursement_envelope_response, error = bridge_disbursement_helper.create_disbursement_envelope(
                disbursement_envelope_request_message
            )
            _logger.debug(
                f"Disbursement envelope response: {disbursement_envelope_response}"
            )
            if error:
                raise Exception(f"Error occurred while creating envelope: {error}")
            
            disbursement_envelopes = []
            for disbursment_envelope_reponse_message in disbursement_envelope_response.message:
                disbursement_envelope = DisbursementEnvelope(
                    disbursement_envelope_id = disbursment_envelope_reponse_message.disbursement_envelope_id,
                    beneficiary_list_id = beneficiary_list.id,
                    benefit_program_mnemonic = disbursment_envelope_reponse_message.benefit_program_mnemonic,
                    benefit_code_id = int(disbursment_envelope_reponse_message.benefit_code_id),
                    benefit_type = disbursment_envelope_reponse_message.benefit_type.value,
                    cash_distribution_mode = disbursment_envelope_reponse_message.cash_distribution_mode.value,
                    disbursement_cycle_id = int(disbursment_envelope_reponse_message.disbursement_cycle_id),
                    cycle_code_mnemonic = disbursment_envelope_reponse_message.cycle_code_mnemonic,
                    number_of_beneficiaries = disbursment_envelope_reponse_message.number_of_beneficiaries,
                    number_of_disbursements = disbursment_envelope_reponse_message.number_of_disbursements,
                    total_disbursed_quantity = disbursment_envelope_reponse_message.total_disbursement_quantity,
                    measurement_unit = disbursment_envelope_reponse_message.measurement_unit,
                    disbursement_schedule_date = disbursment_envelope_reponse_message.disbursement_schedule_date
                )
                disbursement_envelopes.append(disbursement_envelope)
                _logger.info(
                    f"Envelope creation successful for disbursement envelope id: {disbursment_envelope_reponse_message.disbursement_envelope_id}"
                )

            # Bulk insert all the disbursement envelopes
            eee_session.add_all(disbursement_envelopes)

            beneficiary_list.disbursement_envelope_status = StatusEnum.COMPLETE.value
            beneficiary_list.disbursement_batch_creation_status = StatusEnum.PENDING.value

            pbms_session.commit()
            eee_session.commit()

        except Exception as e:
            _logger.error(
                f"Exception occurred while processing disbursement envelope creation request: {e}"
            )
            if beneficiary_list:
                beneficiary_list.disbursement_envelope_status = StatusEnum.PENDING.value
                pbms_session.commit()
