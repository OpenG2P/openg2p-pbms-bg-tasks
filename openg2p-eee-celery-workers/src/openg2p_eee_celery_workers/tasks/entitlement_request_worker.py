import json
import logging
from datetime import datetime, timezone
from typing import List

from openg2p_eee_models.models import EEEDetails
from openg2p_eee_models.schemas import RegistrantDetails
from openg2p_eee_registry_adapters.factory import EEERegistryFactory
from openg2p_eee_registry_adapters.interface import EEERegistryInterface
from openg2p_pbms_models.models import (
    G2PEntitlementRuleDefinition,
    G2PProgramDefinition,
    G2PQueEEERequest,
    StatusEnum,
)
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="entitlement_request_worker")
def entitlement_request_worker(id: int):
    _logger.info("Starting entitlement list generation")
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
        eee_details = None
        try:
            # Fetch the queue entry from pbms db using id
            eee_details = (
                eee_session.query(EEEDetails)
                .filter(EEEDetails.id == id)
                .first()
            )
            if not eee_details:
                _logger.error(f"No EEEDetails entry found for id: {id}")
                return

            g2p_que_eee_request = (
                pbms_session.query(G2PQueEEERequest)
                .filter(G2PQueEEERequest.pbms_request_id == eee_details.pbms_request_id)
                .first()
            )
            if not g2p_que_eee_request:
                _logger.error(
                    f"No G2PQueEEERequest entry found for pbms_request_id: {eee_details.pbms_request_id}"
                )
                return

            target_registry_type, max_quantity = (
                pbms_session.query(
                    G2PProgramDefinition.target_registry_type,
                    G2PProgramDefinition.max_quantity,
                )
                .filter(G2PProgramDefinition.id == g2p_que_eee_request.program_id)
                .one_or_none()
            )

            entitlement_rule_definitions: List[G2PEntitlementRuleDefinition] = (
                pbms_session.query(G2PEntitlementRuleDefinition)
                .filter(
                    G2PEntitlementRuleDefinition.program_id
                    == g2p_que_eee_request.program_id
                )
                .all()
            )

            registrant_details_list: List[RegistrantDetails] = []

            for registrant_details_json in eee_details.registrant_details:
                registrant_details = RegistrantDetails(**registrant_details_json)

                if max_quantity and (registrant_details.entitlement_quantity == max_quantity):
                    continue
                else:
                    for entitlement_rule_definition in entitlement_rule_definitions:
                        try:
                            eee_registry_interface: EEERegistryInterface = (
                                EEERegistryFactory.get_computation_class(
                                    target_registry_type
                                )
                            )
                            is_registrant_entitled: bool = (
                                eee_registry_interface.get_is_registant_entitled(
                                    registrant_details.registrant_id,
                                    entitlement_rule_definition.sql_query,
                                    sr_session,
                                )
                            )
                            if is_registrant_entitled:
                                registrant_details.entitlement_quantity = (
                                    min(
                                        registrant_details.entitlement_quantity
                                        + entitlement_rule_definition.quantity,
                                        max_quantity,
                                    )
                                    if max_quantity
                                    else (
                                        registrant_details.entitlement_quantity
                                        + entitlement_rule_definition.quantity
                                    )
                                )

                        except Exception as e:
                            _logger.error(
                                f"Error processing entitlement rule id {entitlement_rule_definition.id} for registrant id in request queue id {id}: {e}"
                            )
                            return
                registrant_details_list.append(registrant_details)

                _logger.debug(
                    f"Registrant with id {registrant_details.registrant_id} is entitled for {registrant_details.entitlement_quantity}"
                )
                _logger.info(
                    f"Entitlement processed for registrant_id {registrant_details.registrant_id} for pbms_request_id"
                )

            eee_details.registrant_details = [r.model_dump(mode="json") for r in registrant_details_list]

            eee_details.entitlement_status = StatusEnum.COMPLETE.value
            eee_session.add(eee_details)

            _logger.info(
                f"Computing and updating entitlement summary statistics for pbms_request_id: {eee_details.pbms_request_id}"
            )

            try:
                # Get the appropriate summary computation class
                eee_registry_interface: EEERegistryInterface = (
                    EEERegistryFactory.get_computation_class(target_registry_type)
                )
                eee_registry_interface.lock_and_update_summary(
                    eee_details.number_of_registrants, eee_details.pbms_request_id, eee_session
                )

                # Compute summary and add to session
                eee_registry_interface.compute_entitlements_and_modify_summary(
                    eee_details.pbms_request_id, eee_session
                )

                _logger.info(
                    f"Entitlement summary statistics added successfully for queue id: {id}"
                )

            except Exception as e:
                _logger.error(
                    f"Error computing entitlement summary statistics for queue id {id}: {e}"
                )
                return

            # Update entitlement request queue entry status
            g2p_que_eee_request.entitlement_process_status = StatusEnum.COMPLETE.value
            g2p_que_eee_request.processed_date = datetime.now(timezone.utc)

            eee_session.commit()
            pbms_session.commit()

        except Exception as e:
            error_message = f"Error during processing entitlement request for queue id {id}: {str(e)}"
            _logger.error(error_message)
            raise e
            if g2p_que_eee_request:
                g2p_que_eee_request.processed_date = datetime.now(timezone.utc)
                # queue_entry.task_status = StatusEnum.FAILED
                pbms_session.commit()

        _logger.info(f"Completed processing entitlement request for queue id: {id}")
