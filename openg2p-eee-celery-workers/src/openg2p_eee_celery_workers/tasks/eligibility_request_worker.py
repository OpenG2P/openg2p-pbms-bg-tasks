import logging
from datetime import datetime

from openg2p_eee_models.models import (
    EnumStatus,
    G2PFarmerRegistry,
    G2PProgramDefinition,
    G2PQueEligibilityRequest,
    G2PRegistryType,
    G2PStudentRegistry,
)
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from ..helpers import (
    construct_farmer_summary_statistics,
    construct_intersect_query,
    construct_student_summary_statistics,
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
        queue_entry = None
        try:
            queue_entry = (
                pbms_session.query(G2PQueEligibilityRequest)
                .filter(G2PQueEligibilityRequest.id == id)
                .first()
            )

            if not queue_entry:
                _logger.error(f"No queue entry found for queue id: {id}")
                return
            sql_query_json = queue_entry.sql_query_json
            program_id = queue_entry.program_id

            program = (
                pbms_session.query(G2PProgramDefinition)
                .filter(G2PProgramDefinition.id == program_id)
                .first()
            )
            registrant_type = program.target_registry_type
            program_mnemonic = program.program_mnemonic

            # Construct and execute the SQL query
            constructed_query = construct_intersect_query(sql_query_json)
            result = sr_session.execute(constructed_query).fetchall()

            registrant_ids = [row[0] for row in result]

            # Add entries to g2p_eligibility_details table
            _logger.info(f"Adding eligibility details table for queue id: {id}")
            for registrant_id in registrant_ids:
                eee_session.execute(
                    text(
                        "INSERT INTO g2p_eligibility_details (eligibility_list_id, registrant_id) VALUES (:eligibility_list_id, :registrant_id)"
                    ),
                    {
                        "eligibility_list_id": queue_entry.id,
                        "registrant_id": registrant_id,
                    },
                )

            # Construct summary statistics
            _logger.info(f"Adding summary statistics for queue id: {id}")
            base_summary = {
                "program_id": program_id,
                "program_mnemonic": program_mnemonic,
                "target_registry_type": registrant_type,
                "eligibility_request_id": id,
                "number_of_registrants": len(registrant_ids),
                "date_created": datetime.utcnow(),
            }
            if registrant_type == G2PRegistryType.FARMER.value:
                registrant_data = (
                    sr_session.query(G2PFarmerRegistry)
                    .filter(G2PFarmerRegistry.id.in_(registrant_ids))
                    .all()
                )

                farmer_summary = construct_farmer_summary_statistics(
                    base_summary, registrant_data
                )
                eee_session.add(farmer_summary)

            elif registrant_type == G2PRegistryType.STUDENT.value:
                registrant_data = (
                    sr_session.query(G2PStudentRegistry)
                    .filter(G2PStudentRegistry.id.in_(registrant_ids))
                    .all()
                )

                student_summary = construct_student_summary_statistics(
                    base_summary, registrant_data
                )
                eee_session.add(student_summary)

            else:
                _logger.error(
                    f"Invalid registrant type set for program_id: {program_id}"
                )

            eee_session.commit()

            # Update queue entry statuses
            queue_entry.enumeration_status = EnumStatus.COMPLETE.value
            queue_entry.processed_date = datetime.utcnow()

            pbms_session.commit()

        except Exception as e:
            error_message = f"Error during processing eligibility request for queue id {id}: {str(e)}"
            _logger.error(error_message)

            if queue_entry:
                queue_entry.processed_date = datetime.utcnow()
                # queue_entry.task_status = EnumStatus.FAILED
                pbms_session.commit()

        _logger.info(f"Completed processing eligibility request for queue id: {id}")
