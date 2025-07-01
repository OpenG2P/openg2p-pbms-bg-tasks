import json
import logging
from datetime import datetime, timezone
from typing import List

from openg2p_bg_task_models.models import BeneficiaryListDetails
from openg2p_bg_task_models.schemas import RegistrantDetails
from openg2p_bg_task_registry_adapters.factory import RegistryFactory
from openg2p_bg_task_registry_adapters.interface import RegistryInterface
from openg2p_pbms_models.models import (
    G2PBeneficiaryList,
    G2PEntitlementRuleDefinition,
    G2PProgramBenefitCodes,
    G2PProgramDefinition,
    StatusEnum,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)
_engine = get_engine()


@celery_app.task(name="entitlement_worker")
def entitlement_worker(id: str):
    _logger.info("Starting entitlement list generation")
    bg_task_session_maker = sessionmaker(
        bind=_engine.get("db_engine_bg_task"), expire_on_commit=False
    )
    sr_session_maker = sessionmaker(
        bind=_engine.get("db_engine_sr"), expire_on_commit=False
    )
    pbms_session_maker = sessionmaker(
        bind=_engine.get("db_engine_pbms"), expire_on_commit=False
    )

    with bg_task_session_maker() as bg_task_session, sr_session_maker() as sr_session, pbms_session_maker() as pbms_session:
        beneficiary_list_details = None
        try:
            # Fetch the beneficiary list entry from pbms db using id
            beneficiary_list_details = (
                bg_task_session.query(BeneficiaryListDetails)
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

            target_registry = (
                pbms_session.query(G2PProgramDefinition.target_registry)
                .filter(G2PProgramDefinition.id == beneficiary_list.program_id)
                .one_or_none()
            )
            target_registry = target_registry[0]
            _logger.info(f"target_registry {target_registry}")

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
                registrant_detail = RegistrantDetails(**registrant_detail)

                for entitlement_rule_definition in entitlement_rule_definitions:
                    benefit_code_id = entitlement_rule_definition.benefit_code_id
                    program_benefit_code_max_quantity = (
                        pbms_session.query(G2PProgramBenefitCodes.max_quantity)
                        .filter(
                            G2PProgramBenefitCodes.program_id
                            == beneficiary_list.program_id,
                            G2PProgramBenefitCodes.benefit_code_id == benefit_code_id,
                        )
                        .first()
                    )
                    max_quantity: float = (
                        program_benefit_code_max_quantity[0]
                        if program_benefit_code_max_quantity
                        else 0
                    )
                    if (
                        registrant_detail.entitlement is not None
                        and benefit_code_id in registrant_detail.entitlement
                        and registrant_detail.entitlement[benefit_code_id]
                        == max_quantity
                    ):
                        continue
                    else:
                        try:
                            registry_interface: RegistryInterface = (
                                RegistryFactory.get_registry_class(target_registry)
                            )
                            is_registrant_entitled: bool = (
                                registry_interface.get_is_registant_entitled(
                                    registrant_detail.registrant_id,
                                    entitlement_rule_definition.sql_query,
                                    sr_session,
                                )
                            )
                            if is_registrant_entitled:
                                calculated_entitlement = calculate_entitlement(
                                    sr_session,
                                    registrant_detail,
                                    entitlement_rule_definition,
                                    registry_interface,
                                )
                                _logger.info(
                                    f"Calculated entitlement: {calculated_entitlement}"
                                )
                                update_registrant_detail_json(
                                    registrant_detail,
                                    entitlement_rule_definition,
                                    benefit_code_id,
                                    max_quantity,
                                    calculated_entitlement,
                                )

                        except Exception as e:
                            _logger.error(
                                f"Error processing entitlement rule id {entitlement_rule_definition.id} for registrant id in request beneficiary list id {id}: {e}"
                            )
                            raise e
                registrant_details_list.append(registrant_detail)

                _logger.debug(
                    f"Registrant with id {registrant_detail.registrant_id} is entitled for entitlement: {registrant_detail.entitlement}"
                )
                _logger.info(
                    f"Entitlement processed for registrant_id {registrant_detail.registrant_id} for beneficiary_list_id"
                )

            beneficiary_list_details.registrant_details = [
                registrant_detail.model_dump(mode="json")
                for registrant_detail in registrant_details_list
            ]

            beneficiary_list_details.entitlement_process_status = (
                StatusEnum.COMPLETE.value
            )

            _logger.info(
                f"Computing and updating entitlement summary statistics for beneficiary_list_id: {beneficiary_list_details.beneficiary_list_id}"
            )
            try:
                beneficiary_list = lock_beneficiary_list(
                    pbms_session, beneficiary_list_details.beneficiary_list_id
                )
                beneficiary_list.number_of_entitlements_processed += (
                    beneficiary_list_details.number_of_registrants
                )

                # Compute entilement statistics if all entitlemts are processed
                if (
                    beneficiary_list.number_of_entitlements_processed
                    == beneficiary_list.number_of_registrants
                ):
                    compute_entitlement_statistics(
                        id,
                        bg_task_session,
                        sr_session,
                        beneficiary_list_details,
                        target_registry,
                    )

                    # Update entitlement request beneficiary list entry status
                    beneficiary_list.entitlement_process_status = (
                        StatusEnum.COMPLETE.value
                    )
                    beneficiary_list.entitlement_processed_date = datetime.now(
                        timezone.utc
                    )

            except Exception:
                return

            bg_task_session.commit()
            pbms_session.commit()

        except Exception as e:
            error_message = f"Error during processing entitlement request for beneficiary list id {id}: {str(e)}"
            _logger.error(error_message)

            bg_task_session.rollback()
            pbms_session.rollback()

            if beneficiary_list and beneficiary_list_details:
                beneficiary_list.entitlement_number_of_attempts += 1
                beneficiary_list.entitlement_process_status = (
                    StatusEnum.PENDING.value
                    if beneficiary_list.entitlement_number_of_attempts
                    < _config.worker_max_attempts
                    else StatusEnum.FAILED.value
                )
                beneficiary_list.entitlement_latest_error_code = str(e)
                beneficiary_list_details.entitlement_process_status = (
                    beneficiary_list.entitlement_process_status
                )
                bg_task_session.commit()
                pbms_session.commit()

        _logger.info(
            f"Completed processing entitlement request for beneficiary list id: {id}"
        )


def compute_entitlement_statistics(
    id, bg_task_session, sr_session, beneficiary_list_details, target_registry
):
    try:
        # Get the appropriate summary computation class
        registry_interface: RegistryInterface = RegistryFactory.get_registry_class(
            target_registry
        )
        registry_interface.compute_entitlement_statistics(
            beneficiary_list_details.beneficiary_list_id,
            bg_task_session,
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


def lock_beneficiary_list(pbms_session: Session, beneficiary_list_id: str):
    beneficiary_list: G2PBeneficiaryList = None
    number_of_lock_attempts: int = 0
    while number_of_lock_attempts < 10:
        try:
            beneficiary_list = (
                pbms_session.query(G2PBeneficiaryList)
                .filter_by(beneficiary_list_id=beneficiary_list_id)
                .with_for_update(nowait=True)
                .one()
            )
            number_of_lock_attempts += 1
        except OperationalError as e:
            raise Exception(
                f"Failed to acquire lock on beneficiary list after {number_of_lock_attempts} attempts: {str(e)}"
            ) from e

    return beneficiary_list


def update_registrant_detail_json(
    registrant_detail,
    entitlement_rule_definition,
    benefit_code_id,
    max_quantity,
    calculated_entitlement,
):
    if benefit_code_id in registrant_detail.entitlement:
        existing_entitlement = registrant_detail.entitlement[benefit_code_id]
        if max_quantity == 0:
            addl_entitlement = existing_entitlement + calculated_entitlement
        else:
            addl_entitlement = min(
                existing_entitlement + calculated_entitlement,
                max_quantity,
            )
        registrant_detail.entitlement[benefit_code_id] = addl_entitlement
    else:
        if max_quantity == 0:
            addl_entitlement = calculated_entitlement
        else:
            addl_entitlement = min(
                calculated_entitlement,
                max_quantity,
            )
        registrant_detail.entitlement[benefit_code_id] = addl_entitlement


def calculate_entitlement(
    sr_session, registrant_detail, entitlement_rule_definition, registry_interface
):
    multiplier: int = 1
    if entitlement_rule_definition.multiplier:
        multiplier = registry_interface.get_entitlement_multiplier(
            entitlement_rule_definition.multiplier,
            registrant_detail.registrant_id,
            sr_session,
        )
    calculated_entitlement = multiplier * entitlement_rule_definition.quantity

    return calculated_entitlement
