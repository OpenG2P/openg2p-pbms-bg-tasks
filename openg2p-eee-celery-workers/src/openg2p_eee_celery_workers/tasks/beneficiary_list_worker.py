import json
import logging
from datetime import datetime, timezone

from openg2p_eee_models.models import BeneficiaryListSummary, BeneficiaryListDetails
from openg2p_eee_models.schemas import RegistrantDetails
from openg2p_eee_registry_adapters.factory import EEERegistryFactory
from openg2p_eee_registry_adapters.interface import EEERegistryInterface
from openg2p_pbms_models.models import (
    G2PEligibilityRuleDefinition,
    G2PProgramDefinition,
    G2PPriorityRuleDefinition,
    G2PBeneficiaryList,
    StatusEnum,
    ListStageEnum,
    ListWorkflowStatusEnum,
)
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from ..helpers import (
    construct_priority_query,
    construct_eligibility_query,
    persist_beneficiary_list_details,
)

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="beneficiary_list_worker")
def beneficiary_list_worker(id: int):
    _logger.info("Starting eligibility list generation")
    eee_session_maker = sessionmaker(
        bind=_engine.get("db_engine_eee"), expire_on_commit=False
    )
    sr_session_maker = sessionmaker(
        bind=_engine.get("db_engine_sr"), expire_on_commit=False
    )
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )

    with eee_session_maker() as eee_session, sr_session_maker() as sr_session, pbms_session_maker() as pbms_session:
        beneficiary_list = None
        try:
            # Fetch the queue entry from pbms db using id
            beneficiary_list = (
                pbms_session.query(G2PBeneficiaryList)
                .filter(G2PBeneficiaryList.id == id)
                .first()
            )

            if not beneficiary_list:
                _logger.error(f"No entry found for beneficiary list id: {id}")
                return

            g2p_program_definition = (
                pbms_session.query(G2PProgramDefinition)
                .filter(G2PProgramDefinition.id == beneficiary_list.program_id)
                .first()
            )

            constructed_query = None

            if beneficiary_list.list_stage == ListStageEnum.ENROLLMENT.value:
                sql_queries = (
                    pbms_session.execute(
                        select(G2PEligibilityRuleDefinition.sql_query).where(
                            G2PEligibilityRuleDefinition.program_id
                            == beneficiary_list.program_id
                        )
                    )
                    .scalars()
                    .all()
                )

                constructed_query = construct_eligibility_query(sql_queries)

            elif beneficiary_list.list_stage == ListStageEnum.DISBURSEMENT.value:
                # Get the beneficiary_list_id of the latest APPROVED FINAL ENROLMENT in the same program
                latest_approved_final_enrollment_beneficiary_list_id = (
                    pbms_session.query(G2PBeneficiaryList.beneficiary_list_id)
                    .filter(
                        G2PBeneficiaryList.program_id == beneficiary_list.program_id,
                        G2PBeneficiaryList.list_stage == ListStageEnum.ENROLLMENT.value,
                        G2PBeneficiaryList.list_workflow_status == ListWorkflowStatusEnum.APPROVED_FINAL_ENROLMENT.value,
                    )
                    .order_by(G2PBeneficiaryList.creation_date.desc())
                    .scalar()
                )

                # Get the registrant_details field from beneficiary_list_details for the latest approved final enrollment
                approved_registrant_details = None
                if latest_approved_final_enrollment_beneficiary_list_id:
                    latest_beneficiary_list_details = (
                        eee_session.execute(
                            select(BeneficiaryListDetails.registrant_details).where(
                                BeneficiaryListDetails.beneficiary_list_id
                                == latest_approved_final_enrollment_beneficiary_list_id
                            )
                        )
                        .scalars()
                        .all()
                    )
                    if latest_beneficiary_list_details:
                        approved_registrant_details = latest_beneficiary_list_details

                # Unpack approved_registrant_details and extract registrant_ids
                # push to another worker for processing priority rule and entitlement on existing registrant_ids
                registrant_ids = []
                for approved_registrant_detail in approved_registrant_details:
                    if approved_registrant_detail:
                        if isinstance(approved_registrant_detail, str):
                            details_list = json.loads(approved_registrant_detail)
                        else:
                            details_list = approved_registrant_detail
                        registrant_ids = [registrant["registrant_id"] for registrant in details_list]

                sql_queries = (
                    pbms_session.execute(
                        select(G2PPriorityRuleDefinition.sql_query).where(
                            G2PPriorityRuleDefinition.disbursement_cycle_id
                            == beneficiary_list.disbursement_cycle_id
                        )
                    )
                    .scalars()
                    .all()
                )
                constructed_query = construct_priority_query(sql_queries, registrant_ids)

            else:
                _logger.error(
                    f"Invalid list stage {beneficiary_list.list_stage} for beneficiary list id {id}"
                )
            _logger.debug(
                f"Constructed sql query for beneficiary list id {id} is: {constructed_query}"
            )

            total_number_of_registrants = 0
            beneficiary_list_details = []
            cursor = sr_session.execute(constructed_query)
            while True:
                number_of_registrants_for_batch = 0
                beneficiary_list_batch = cursor.fetchmany(_config.disbursement_batch_size)
                registrant_details = []
                if not beneficiary_list_batch:
                    break
                for row in beneficiary_list_batch:
                    number_of_registrants_for_batch += 1
                    registrant_details.append(
                        RegistrantDetails(
                            registrant_id=row[0],
                            entitlement={},
                        ).model_dump(mode="json")
                    )

                total_number_of_registrants += number_of_registrants_for_batch
                beneficiary_list_details.append(
                    BeneficiaryListDetails(
                        beneficiary_list_id=beneficiary_list.beneficiary_list_id,
                        registrant_details=json.dumps(registrant_details),
                        entitlement_status=StatusEnum.PENDING.value if beneficiary_list.list_stage == ListStageEnum.DISBURSEMENT.value else StatusEnum.NOT_APPLICABLE.value,
                        number_of_registrants=number_of_registrants_for_batch,
                    )
                )
            _logger.debug(
                f"Count of registrant IDs for beneficiary list id {id} are: {total_number_of_registrants}"
            )
            _logger.info(f"Adding eligibility details for beneficiary list id: {id}")
            eee_session.add_all(beneficiary_list_details)


            _logger.info(f"Computing and adding summary statistics for beneficiary list id: {id}")

            # Create base summary object
            base_summary = BeneficiaryListSummary(
                program_id=beneficiary_list.program_id,
                program_mnemonic=g2p_program_definition.program_mnemonic,
                target_registry_type=g2p_program_definition.target_registry_type,
                beneficiary_list_id=beneficiary_list.beneficiary_list_id,
                number_of_registrants=total_number_of_registrants,
                date_created=datetime.now(timezone.utc),
            )
            _logger.debug(f"Base summary for beneficiary list id {id} is: {base_summary}")

            try:
                # Get the appropriate summary computation class
                summary_computation_interface: EEERegistryInterface = (
                    EEERegistryFactory.get_registry_class(
                        g2p_program_definition.target_registry_type
                    )
                )

                # Compute summary and add to session
                summary_computation_interface.compute_and_persist_summary(
                    beneficiary_list_details, base_summary, sr_session, eee_session
                )

                _logger.info(
                    f"Summary statistics added successfully for beneficiary list id: {id}"
                )

            except ValueError as e:
                _logger.error(
                    f"Invalid registrant type for program_id {beneficiary_list.program_id}: {e}"
                )
                return

            except Exception as e:
                _logger.error(
                    f"Error computing summary statistics for beneficiary list id {id}: {e}"
                )
                return

            # Update beneficiary list entry status
            beneficiary_list.eligibility_process_status = StatusEnum.COMPLETE.value

            if beneficiary_list.list_stage == ListStageEnum.DISBURSEMENT.value:
                beneficiary_list.entitlement_process_status = StatusEnum.PENDING.value

            beneficiary_list.processed_date = datetime.now(timezone.utc)

            eee_session.commit()
            pbms_session.commit()

        except Exception as e:
            error_message = f"Error during processing eligibility request for beneficiary list id {id}: {str(e)}"
            _logger.error(error_message)

            if beneficiary_list:
                beneficiary_list.processed_date = datetime.now(timezone.utc)
                # queue_entry.task_status = StatusEnum.FAILED
                pbms_session.commit()

        _logger.info(f"Completed processing eligibility request for beneficiary list id: {id}")
