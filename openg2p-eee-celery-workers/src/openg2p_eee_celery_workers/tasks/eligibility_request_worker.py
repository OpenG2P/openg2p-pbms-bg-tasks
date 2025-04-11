import json
import logging
from datetime import datetime, timezone

from openg2p_eee_models.models import EEESummary
from openg2p_eee_models.schemas import RegistrantDetails
from openg2p_eee_registry_adapters.factory import EEERegistryFactory
from openg2p_eee_registry_adapters.interface import EEERegistryInterface
from openg2p_pbms_models.models import (
    G2PEligibilityRuleDefinition,
    G2PProgramDefinition,
    G2PQueEEERequest,
    StatusEnum,
)
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from ..helpers import (
    construct_intersect_query,
    persist_eee_details,
)

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="eligibility_request_worker")
def eligibility_request_worker(id: int):
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
        g2p_que_eee_request = None
        try:
            # Fetch the queue entry from pbms db using id
            g2p_que_eee_request = (
                pbms_session.query(G2PQueEEERequest)
                .filter(G2PQueEEERequest.id == id)
                .first()
            )

            if not g2p_que_eee_request:
                _logger.error(f"No queue entry found for queue id: {id}")
                return

            g2p_program_definition = (
                pbms_session.query(G2PProgramDefinition)
                .filter(G2PProgramDefinition.id == g2p_que_eee_request.program_id)
                .first()
            )
            # TODO: get sql_query from eligibility_definition table
            # since it is not stored in que_eee_request table anymore
            sql_queries = (
                pbms_session.execute(
                    select(G2PEligibilityRuleDefinition.sql_query).where(
                        G2PEligibilityRuleDefinition.program_id
                        == g2p_que_eee_request.program_id
                    )
                )
                .scalars()
                .all()
            )

            # Construct and execute the SQL query
            constructed_query = construct_intersect_query(sql_queries)
            _logger.debug(
                f"Constructed eligibility list generation sql query for queue id {id} is: {constructed_query}"
            )

            total_number_of_registrants = 0
            eee_details = []
            cursor = sr_session.execute(constructed_query)
            while True:
                number_of_registrants_for_batch = 0
                batch = cursor.fetchmany(_config.disbursement_batch_size)
                registrant_details = []
                if not batch:
                    break
                for row in batch:
                    number_of_registrants_for_batch += 1
                    registrant_details.append(RegistrantDetails(
                        registrant_id=row[0],
                        entitlement_quantity=0,
                    ).model_dump(mode="json"))

                total_number_of_registrants += number_of_registrants_for_batch
                eee_details.append(
                    {
                        "pbms_request_id": g2p_que_eee_request.pbms_request_id,
                        "registrant_details": json.dumps(registrant_details),
                        "entitlement_status": StatusEnum.PENDING.value,
                        "number_of_registrants": number_of_registrants_for_batch,
                    }
                )

            _logger.info(f"Adding eligibility details for queue id: {id}")
            persist_eee_details(
                eee_details, eee_session
            )

            _logger.debug(
                f"Count of registrant IDs for queue id {id} are: {total_number_of_registrants}"
            )

            _logger.info(f"Computing and adding summary statistics for queue id: {id}")

            # Create base summary object
            base_summary = EEESummary(
                program_id=g2p_que_eee_request.program_id,
                program_mnemonic=g2p_program_definition.program_mnemonic,
                target_registry_type=g2p_program_definition.target_registry_type,
                pbms_request_id=g2p_que_eee_request.pbms_request_id,
                number_of_registrants=total_number_of_registrants,
                date_created=datetime.now(timezone.utc),
            )
            _logger.debug(f"Base summary for queue id {id} is: {base_summary}")

            try:
                # Get the appropriate summary computation class
                summary_computation_interface: EEERegistryInterface = (
                    EEERegistryFactory.get_computation_class(
                        g2p_program_definition.target_registry_type
                    )
                )

                # Compute summary and add to session
                summary_computation_interface.compute_and_persist_summary(
                    eee_details, base_summary, sr_session, eee_session
                )

                _logger.info(
                    f"Summary statistics added successfully for queue id: {id}"
                )

            except ValueError as e:
                _logger.error(
                    f"Invalid registrant type for program_id {g2p_que_eee_request.program_id}: {e}"
                )
                return

            except Exception as e:
                _logger.error(
                    f"Error computing summary statistics for queue id {id}: {e}"
                )
                return

            # Update eligibility request queue entry status
            g2p_que_eee_request.eligibility_process_status = StatusEnum.COMPLETE.value
            g2p_que_eee_request.entitlement_process_status = StatusEnum.PENDING.value
            g2p_que_eee_request.processed_date = datetime.now(timezone.utc)

            eee_session.commit()
            pbms_session.commit()

        except Exception as e:
            error_message = f"Error during processing eligibility request for queue id {id}: {str(e)}"
            _logger.error(error_message)

            if g2p_que_eee_request:
                g2p_que_eee_request.processed_date = datetime.now(timezone.utc)
                # queue_entry.task_status = StatusEnum.FAILED
                pbms_session.commit()

        _logger.info(f"Completed processing eligibility request for queue id: {id}")
