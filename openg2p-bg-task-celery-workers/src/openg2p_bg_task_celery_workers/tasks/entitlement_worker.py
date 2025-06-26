import json
import logging
from datetime import datetime, timezone
from typing import List

from openg2p_bg_task_models.models import BeneficiaryListDetails
from openg2p_bg_task_models.schemas import RegistrantDetails
from openg2p_bg_task_registry_adapters.factory import EEERegistryFactory
from openg2p_bg_task_registry_adapters.interface import EEERegistryInterface
from openg2p_pbms_models.models import (
    G2PBeneficiaryList,
    G2PEntitlementRuleDefinition,
    G2PProgramDefinition,
    StatusEnum,
)
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="entitlement_worker")
def entitlement_worker(id: int):
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
        beneficiary_list_details = None
        try:
            # Fetch the beneficiary list entry from pbms db using id
            beneficiary_list_details = (
                eee_session.query(BeneficiaryListDetails)
                .filter(BeneficiaryListDetails.id == id)
                .first()
            )
            if not beneficiary_list_details:
                _logger.error(f"No BeneficiaryListDetails entry found for id: {id}")
                return

            beneficiary_list = (
                pbms_session.query(G2PBeneficiaryList)
                .filter(
                    G2PBeneficiaryList.beneficiary_list_id
                    == beneficiary_list_details.beneficiary_list_id
                )
                .first()
            )
            if not beneficiary_list:
                _logger.error(
                    f"No G2PBeneficiaryList entry found for beneficiary_list_id: {beneficiary_list_details.beneficiary_list_id}"
                )
                return

            target_registry_type = (
                pbms_session.query(G2PProgramDefinition.target_registry_type)
                .filter(G2PProgramDefinition.id == beneficiary_list.program_id)
                .one_or_none()
            )
            target_registry_type = target_registry_type[0]
            _logger.info(f"target_registry {target_registry_type}")

            entitlement_rule_definitions: List[G2PEntitlementRuleDefinition] = (
                pbms_session.query(G2PEntitlementRuleDefinition)
                .filter(
                    G2PEntitlementRuleDefinition.program_id
                    == beneficiary_list.program_id
                )
                .all()
            )

            registrant_details_list: List[RegistrantDetails] = []

            for registrant_detail in json.loads(
                beneficiary_list_details.registrant_details
            ):
                registrant_details = RegistrantDetails(**registrant_detail)

                for entitlement_rule_definition in entitlement_rule_definitions:
                    benefit_code_id = entitlement_rule_definition.benefit_code_id
                    if (
                        registrant_details.entitlement is not None
                        and benefit_code_id in registrant_details.entitlement
                        and registrant_details.entitlement[benefit_code_id]
                        == entitlement_rule_definition.max_quantity
                    ):
                        continue
                    else:
                        try:
                            eee_registry_interface: EEERegistryInterface = (
                                EEERegistryFactory.get_registry_class(
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
                                multiplier: int = (
                                    eee_registry_interface.get_entitlement_multiplier(
                                        entitlement_rule_definition.multiplier,
                                        registrant_details.registrant_id,
                                        sr_session,
                                    )
                                )
                                calculated_entitlement = (
                                    multiplier * entitlement_rule_definition.quantity
                                )
                                _logger.info(
                                    f"calculated entitlement: {calculated_entitlement}"
                                )

                                if benefit_code_id in registrant_details.entitlement:
                                    _logger.info(f"benefit code id: {benefit_code_id}")
                                    _logger.info(
                                        f"entitlement: {registrant_details.entitlement}"
                                    )
                                    existing_entitlement = (
                                        registrant_details.entitlement[benefit_code_id]
                                    )
                                    if entitlement_rule_definition.max_quantity == 0:
                                        addl_entitlement = (
                                            existing_entitlement
                                            + calculated_entitlement
                                        )
                                    else:
                                        addl_entitlement = min(
                                            existing_entitlement
                                            + calculated_entitlement,
                                            entitlement_rule_definition.max_quantity,
                                        )
                                    registrant_details.entitlement[
                                        benefit_code_id
                                    ] = addl_entitlement
                                else:
                                    if entitlement_rule_definition.max_quantity == 0:
                                        addl_entitlement = calculated_entitlement
                                    else:
                                        addl_entitlement = min(
                                            calculated_entitlement,
                                            entitlement_rule_definition.max_quantity,
                                        )
                                    registrant_details.entitlement[
                                        benefit_code_id
                                    ] = addl_entitlement

                        except Exception as e:
                            _logger.error(
                                f"Error processing entitlement rule id {entitlement_rule_definition.id} for registrant id in request beneficiary list id {id}: {e}"
                            )
                            raise e
                            return
                registrant_details_list.append(registrant_details)

                _logger.debug(
                    f"Registrant with id {registrant_details.registrant_id} is entitled for entitlement: {registrant_details.entitlement}"
                )
                _logger.info(
                    f"Entitlement processed for registrant_id {registrant_details.registrant_id} for beneficiary_list_id"
                )

            beneficiary_list_details.registrant_details = [
                r.model_dump(mode="json") for r in registrant_details_list
            ]

            beneficiary_list_details.entitlement_status = StatusEnum.COMPLETE.value
            eee_session.add(beneficiary_list_details)

            _logger.info(
                f"Computing and updating entitlement summary statistics for beneficiary_list_id: {beneficiary_list_details.beneficiary_list_id}"
            )

            try:
                # Get the appropriate summary computation class
                eee_registry_interface: EEERegistryInterface = (
                    EEERegistryFactory.get_registry_class(target_registry_type)
                )
                eee_registry_interface.lock_and_update_summary(
                    beneficiary_list_details.number_of_registrants,
                    beneficiary_list_details.beneficiary_list_id,
                    eee_session,
                )

                # Compute summary and add to session
                eee_registry_interface.compute_entitlements_and_modify_summary(
                    beneficiary_list_details.beneficiary_list_id,
                    eee_session,
                    sr_session,
                )

                _logger.info(
                    f"Entitlement summary statistics added successfully for beneficiary list id: {id}"
                )

            except Exception as e:
                _logger.error(
                    f"Error computing entitlement summary statistics for beneficiary list id {id}: {e}"
                )
                return

            # Update entitlement request beneficiary list entry status
            beneficiary_list.entitlement_process_status = StatusEnum.COMPLETE.value
            beneficiary_list.processed_date = datetime.now(timezone.utc)

            eee_session.commit()
            pbms_session.commit()

        except Exception as e:
            error_message = f"Error during processing entitlement request for beneficiary list id {id}: {str(e)}"
            _logger.error(error_message)
            if beneficiary_list:
                beneficiary_list.processed_date = datetime.now(timezone.utc)
                # queue_entry.task_status = StatusEnum.FAILED
                pbms_session.commit()

        _logger.info(
            f"Completed processing entitlement request for beneficiary list id: {id}"
        )
