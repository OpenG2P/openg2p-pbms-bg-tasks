import json
import logging
from datetime import date
from typing import Dict, List, Optional

import numpy as np
from fastapi_cache.decorator import cache
from openg2p_bg_task_models.models import BeneficiaryListDetails
from openg2p_bg_task_models.schemas import (
    BeneficiarySearchResponsePayload,
    RegistrantDetails,
)
from openg2p_pbms_models.models import Gender
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ..cache import beneficiary_count_key_builder
from ..interface import RegistryInterface
from ..models import (
    BeneficiaryListSummaryStudent as BeneficiaryListSummaryStudentModel,
)
from ..models import (
    G2PStudentRegistry,
)
from ..schema import (
    BeneficiaryListSummary,
    BeneficiaryListSummaryStudent,
    BeneficiaryListSummaryStudentPayload,
    G2PStudentRegistryPayload,
)

_logger = logging.getLogger("openg2p_bg_task_registry_adapters")


class RegistryStudent(RegistryInterface):
    """Fetches student data and computes summary statistics"""

    # ===================
    # Summary API Methods
    # ===================
    async def get_summary(
        self, beneficiary_list_id: int, bg_task_session: AsyncSession
    ) -> BeneficiaryListSummaryStudentPayload:
        _logger.info(f"Fetching summary for beneficiary_list_id: {beneficiary_list_id}")
        eligibility_summary_student = await bg_task_session.execute(
            select(BeneficiaryListSummaryStudentModel).where(
                BeneficiaryListSummaryStudentModel.beneficiary_list_id
                == beneficiary_list_id
            )
        )
        eligibility_summary_student = eligibility_summary_student.scalars().first()

        if not eligibility_summary_student:
            raise ValueError(
                f"No summary found for beneficiary_list_id: {beneficiary_list_id}"
            )

        summary = BeneficiaryListSummaryStudentPayload(
            beneficiary_list_summary=BeneficiaryListSummary(
                id=eligibility_summary_student.id,
                program_id=eligibility_summary_student.program_id,
                program_mnemonic=eligibility_summary_student.program_mnemonic,
                target_registry=eligibility_summary_student.target_registry,
                beneficiary_list_id=eligibility_summary_student.beneficiary_list_id,
                number_of_registrants=format(
                    eligibility_summary_student.number_of_registrants, ","
                ),
                date_created=eligibility_summary_student.date_created,
                total_disbursement_quantity=format(
                    eligibility_summary_student.total_disbursement_quantity, ","
                )
                + " "
                + eligibility_summary_student.entitlement_units,
                average_entitlement_per_registrant=format(
                    eligibility_summary_student.average_entitlement_per_person, ","
                )
                + " "
                + eligibility_summary_student.entitlement_units,
            ),
            registry_summary=BeneficiaryListSummaryStudent(
                age_mean=f"{eligibility_summary_student.age_mean} {eligibility_summary_student.age_units}"
                if eligibility_summary_student.age_mean is not None
                else None,
                age_quartile_25=f"{eligibility_summary_student.age_quartile_25} {eligibility_summary_student.age_units}"
                if eligibility_summary_student.age_quartile_25 is not None
                else None,
                age_quartile_50=f"{eligibility_summary_student.age_quartile_50} {eligibility_summary_student.age_units}"
                if eligibility_summary_student.age_quartile_50 is not None
                else None,
                age_quartile_75=f"{eligibility_summary_student.age_quartile_75} {eligibility_summary_student.age_units}"
                if eligibility_summary_student.age_quartile_75 is not None
                else None,
                average_entitlement_female=eligibility_summary_student.average_entitlement_female,
                average_entitlement_male=eligibility_summary_student.average_entitlement_male,
                entitlement_amount_q1=eligibility_summary_student.entitlement_amount_q1,
                entitlement_amount_q2=eligibility_summary_student.entitlement_amount_q2,
                entitlement_amount_q3=eligibility_summary_student.entitlement_amount_q3,
                entitlement_amount_male_q1=eligibility_summary_student.entitlement_amount_male_q1,
                entitlement_amount_male_q2=eligibility_summary_student.entitlement_amount_male_q2,
                entitlement_amount_male_q3=eligibility_summary_student.entitlement_amount_male_q3,
                entitlement_amount_female_q1=eligibility_summary_student.entitlement_amount_female_q1,
                entitlement_amount_female_q2=eligibility_summary_student.entitlement_amount_female_q2,
                entitlement_amount_female_q3=eligibility_summary_student.entitlement_amount_female_q3,
            ),
        )

        return summary

    def get_summary_sync(
        self, beneficiary_list_id: str, bg_task_session: Session
    ) -> BeneficiaryListSummaryStudentPayload:
        eligibility_summary_student = (
            bg_task_session.query(BeneficiaryListSummaryStudentModel)
            .filter_by(beneficiary_list_id=beneficiary_list_id)
            .first()
        )

        if not eligibility_summary_student:
            raise ValueError(
                f"No summary found for beneficiary_list_id: {beneficiary_list_id}"
            )

        summary = BeneficiaryListSummaryStudentPayload(
            beneficiary_list_summary=BeneficiaryListSummary(
                id=eligibility_summary_student.id,
                program_id=eligibility_summary_student.program_id,
                program_mnemonic=eligibility_summary_student.program_mnemonic,
                target_registry=eligibility_summary_student.target_registry,
                beneficiary_list_id=eligibility_summary_student.beneficiary_list_id,
                number_of_registrants=eligibility_summary_student.number_of_registrants,
                date_created=eligibility_summary_student.date_created,
                total_disbursement_quantity=eligibility_summary_student.total_disbursement_quantity,
                average_entitlement_per_registrant=eligibility_summary_student.average_entitlement_per_person,
            ),
            registry_summary=BeneficiaryListSummaryStudent(
                age_mean=f"{eligibility_summary_student.age_mean} {eligibility_summary_student.age_units}"
                if eligibility_summary_student.age_mean is not None
                else None,
                age_quartile_25=f"{eligibility_summary_student.age_quartile_25} {eligibility_summary_student.age_units}"
                if eligibility_summary_student.age_quartile_25 is not None
                else None,
                age_quartile_50=f"{eligibility_summary_student.age_quartile_50} {eligibility_summary_student.age_units}"
                if eligibility_summary_student.age_quartile_50 is not None
                else None,
                age_quartile_75=f"{eligibility_summary_student.age_quartile_75} {eligibility_summary_student.age_units}"
                if eligibility_summary_student.age_quartile_75 is not None
                else None,
                average_entitlement_female=eligibility_summary_student.average_entitlement_female,
                average_entitlement_male=eligibility_summary_student.average_entitlement_male,
                entitlement_amount_q1=eligibility_summary_student.entitlement_amount_q1,
                entitlement_amount_q2=eligibility_summary_student.entitlement_amount_q2,
                entitlement_amount_q3=eligibility_summary_student.entitlement_amount_q3,
                entitlement_amount_male_q1=eligibility_summary_student.entitlement_amount_male_q1,
                entitlement_amount_male_q2=eligibility_summary_student.entitlement_amount_male_q2,
                entitlement_amount_male_q3=eligibility_summary_student.entitlement_amount_male_q3,
                entitlement_amount_female_q1=eligibility_summary_student.entitlement_amount_female_q1,
                entitlement_amount_female_q2=eligibility_summary_student.entitlement_amount_female_q2,
                entitlement_amount_female_q3=eligibility_summary_student.entitlement_amount_female_q3,
            ),
        )

        return summary

    # ==============================
    # Beneficiary Search API Methods
    # ==============================
    async def search_beneficiaries(
        self,
        bg_task_session: AsyncSession,
        sr_session: AsyncSession,
        beneficiary_list_id: str,
        target_registry: str,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        order_by: str = "id asc",
    ) -> BeneficiarySearchResponsePayload:
        registrant_details_result = await bg_task_session.execute(
            select(BeneficiaryListDetails.registrant_details).where(
                BeneficiaryListDetails.beneficiary_list_id == beneficiary_list_id
            )
        )
        registrant_details = registrant_details_result.scalars().all()
        registrant_ids = []
        for registrant_detail in registrant_details:
            for registrant in registrant_detail:
                registrant_ids.append(registrant["registrant_id"])

        (
            student_search_query,
            student_search_params,
        ) = self.construct_beneficiary_search_sql_query(
            registrant_ids,
            target_registry,
            search_query,
            order_by,
            page_size,
            page,
        )
        student_search_results = (
            (await sr_session.execute(student_search_query, student_search_params))
            .mappings()
            .all()
        )

        total_beneficiary_count = await self._get_total_beneficiary_count(
            sr_session, beneficiary_list_id, registrant_ids, search_query
        )

        beneficiaries = []
        if student_search_results:
            beneficiaries = [
                G2PStudentRegistryPayload(
                    id=student["id"],
                    unique_id=student["unique_id"],
                    registration_date=student["registration_date"],
                    name=student["name"],
                    institution_name=student["institution_name"],
                    date_of_birth=student["date_of_birth"],
                )
                for student in student_search_results
            ]

        response_payload = BeneficiarySearchResponsePayload(
            total_beneficiary_count=total_beneficiary_count,
            page=page,
            page_size=page_size,
            beneficiaries=beneficiaries,
        )

        return response_payload

    @cache(expire=120, key_builder=beneficiary_count_key_builder)
    async def _get_total_beneficiary_count(
        self,
        sr_session: AsyncSession,
        beneficiary_list_id: str,
        registrant_ids: List[str],
        search_query: Optional[str] = None,
    ) -> int:
        (
            beneficiary_count_query,
            beneficiary_count_params,
        ) = self.construct_beneficiary_search_count_sql_query(
            registrant_ids, "student", search_query
        )
        total_beneficiary_count = (
            await sr_session.execute(beneficiary_count_query, beneficiary_count_params)
        ).scalar_one()

        return total_beneficiary_count

    # =================================
    # Eligibility Celery Worker Methods
    # =================================
    def compute_eligibility_statistics(
        self,
        beneficiary_list_details: List[dict],
        base_summary,
        sr_session: Session,
        bg_task_session: Session,
    ):
        students_age = []

        for beneficiary_list_detail in beneficiary_list_details:
            registrant_ids = []
            registrant_details = beneficiary_list_detail.get("registrant_details")
            if isinstance(registrant_details, str):
                registrant_details = json.loads(registrant_details)
            for registrant in registrant_details:
                registrant_ids.append(registrant["registrant_id"])

            registrants = self.get_registrants_by_ids(registrant_ids, sr_session)
            for student in registrants:
                students_age.append(self.calculate_age(student.date_of_birth))

        student_summary = BeneficiaryListSummaryStudentModel(
            program_id=base_summary.program_id,
            program_mnemonic=base_summary.program_mnemonic,
            target_registry=base_summary.target_registry,
            beneficiary_list_id=base_summary.beneficiary_list_id,
            number_of_registrants=base_summary.number_of_registrants,
            date_created=base_summary.date_created,
        )

        if students_age:
            students_age_array = np.array(students_age)
            student_summary.age_quartile_25 = round(
                float(np.percentile(students_age_array, 25, method="midpoint")), 2
            )
            student_summary.age_quartile_50 = round(
                float(np.percentile(students_age_array, 50, method="midpoint")), 2
            )
            student_summary.age_quartile_75 = round(
                float(np.percentile(students_age_array, 75, method="midpoint")), 2
            )
            student_summary.age_mean = round(float(np.mean(students_age_array)), 2)

        bg_task_session.add(student_summary)

    def get_registrants_by_ids(
        self, registrant_ids: List[str], sr_session: Session
    ) -> List[G2PStudentRegistry]:
        if not registrant_ids:
            return []
        return (
            sr_session.query(G2PStudentRegistry)
            .filter(G2PStudentRegistry.unique_id.in_(registrant_ids))
            .all()
        )

    @staticmethod
    def calculate_age(birth_date) -> int:
        today = date.today()
        return (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )

    # =================================
    # Entitlement Celery Worker Methods
    # =================================
    def lock_and_update_summary(
        self,
        number_of_registrants: int,
        beneficiary_list_id: str,
        bg_task_session: Session,
    ) -> None:
        try:
            summary_student = (
                bg_task_session.query(BeneficiaryListSummaryStudentModel)
                .filter_by(beneficiary_list_id=beneficiary_list_id)
                .with_for_update()
                .one()
            )
            summary_student.number_of_entitlements_processed += number_of_registrants
            bg_task_session.commit()
        except Exception as e:
            _logger.error(f"Error in lock_and_update_summary: {e}")
            bg_task_session.rollback()

    def get_is_registant_entitled(
        self, registrant_id: str, sql_query: str, sr_session: Session
    ) -> bool:
        sql_query_with_registrant_id = (
            self.construct_get_is_registrant_entitled_sql_query(
                registrant_id, "student", sql_query
            )
        )
        result = sr_session.execute(sql_query_with_registrant_id).fetchone()
        return result is not None

    def get_entitlement_multiplier(
        self, multiplier: str, registrant_id: str, sr_session: Session
    ) -> int:
        if not multiplier or multiplier == "none":
            return 1

        sql_query = self.construct_multiplier_sql_query(
            multiplier, target_registry="student"
        )
        params = {"registrant_id": registrant_id}
        result = sr_session.execute(sql_query, params).fetchone()
        if result is None or result[0] is None:
            return 1
        return int(result[0])

    def compute_entitlement_statistics(
        self, beneficiary_list_id: str, bg_task_session: Session, sr_session: Session
    ):
        summary_student = (
            bg_task_session.query(BeneficiaryListSummaryStudentModel)
            .filter_by(beneficiary_list_id=beneficiary_list_id)
            .first()
        )

        if not summary_student:
            raise ValueError(
                f"No summary found for beneficiary_list_id: {beneficiary_list_id}"
            )

        if (
            summary_student.number_of_entitlements_processed
            != summary_student.number_of_registrants
        ):
            return

        beneficiary_list_details = (
            bg_task_session.query(BeneficiaryListDetails)
            .filter_by(beneficiary_list_id=beneficiary_list_id)
            .all()
        )

        registrant_map: Dict[str, G2PStudentRegistry] = {}

        for beneficiary_list_detail in beneficiary_list_details:
            registrant_ids = []
            registrant_details = beneficiary_list_detail.registrant_details
            for registrant_detail in registrant_details:
                registrant_detail_obj = RegistrantDetails(**registrant_detail)
                registrant_ids.append(registrant_detail_obj.registrant_id)

            registrants_list: List[G2PStudentRegistry] = self.get_registrants_by_ids(
                registrant_ids, sr_session
            )

            for registrant in registrants_list:
                registrant_map[str(registrant.unique_id)] = registrant

        # Collect entitlements per benefit_code_id
        entitlements: Dict[int, list[float]] = {}
        entitlements_male: Dict[int, list[float]] = {}
        entitlements_female: Dict[int, list[float]] = {}

        for beneficiary_list_detail in beneficiary_list_details:
            for registrant_detail in beneficiary_list_detail.registrant_details:
                registrant_detail_obj = RegistrantDetails(**registrant_detail)
                registrant = registrant_map.get(
                    str(registrant_detail_obj.registrant_id)
                )
                gender = registrant.gender if registrant else None

                # For students, entitlement is expected to be a dict of benefit_code_id -> value
                for benefit_code_id, value in registrant_detail_obj.entitlement.items():
                    # All entitlements
                    entitlements.setdefault(benefit_code_id, []).append(value)
                    # By gender
                    if gender == Gender.MALE.value:
                        entitlements_male.setdefault(benefit_code_id, []).append(value)
                    elif gender == Gender.FEMALE.value:
                        entitlements_female.setdefault(benefit_code_id, []).append(
                            value
                        )
                    else:
                        # Accept None gender, but skip for gendered stats
                        continue

        # Compute all summary stats per benefit_code_id
        entitlement_stats = self.compute_stats_dict(entitlements)
        entitlement_male_stats = self.compute_stats_dict(entitlements_male)
        entitlement_female_stats = self.compute_stats_dict(entitlements_female)

        bg_task_session.execute(
            update(BeneficiaryListSummaryStudentModel)
            .where(
                BeneficiaryListSummaryStudentModel.beneficiary_list_id
                == beneficiary_list_id
            )
            .values(
                total_disbursement_quantity=dict(entitlement_stats["total"]),
                average_entitlement_per_person=dict(entitlement_stats["average"]),
                entitlement_amount_q1=dict(entitlement_stats["q1"]),
                entitlement_amount_q2=dict(entitlement_stats["q2"]),
                entitlement_amount_q3=dict(entitlement_stats["q3"]),
                average_entitlement_male=dict(entitlement_male_stats["average"]),
                entitlement_amount_male_q1=dict(entitlement_male_stats["q1"]),
                entitlement_amount_male_q2=dict(entitlement_male_stats["q2"]),
                entitlement_amount_male_q3=dict(entitlement_male_stats["q3"]),
                average_entitlement_female=dict(entitlement_female_stats["average"]),
                entitlement_amount_female_q1=dict(entitlement_female_stats["q1"]),
                entitlement_amount_female_q2=dict(entitlement_female_stats["q2"]),
                entitlement_amount_female_q3=dict(entitlement_female_stats["q3"]),
            )
        )

    def compute_stats_dict(
        self, entitlements_dict: Dict[int, list[float]]
    ) -> Dict[str, Dict[int, float]]:
        # Returns a dict of stats per benefit_code_id for each stat
        stats = {
            "average": {},
            "q1": {},
            "q2": {},
            "q3": {},
            "total": {},
        }
        for benefit_code_id, values in entitlements_dict.items():
            if not values:
                stats["average"][benefit_code_id] = 0.0
                stats["q1"][benefit_code_id] = 0.0
                stats["q2"][benefit_code_id] = 0.0
                stats["q3"][benefit_code_id] = 0.0
                stats["total"][benefit_code_id] = 0.0
            else:
                arr = np.array(values)
                stats["average"][benefit_code_id] = round(float(np.mean(arr)), 2)
                stats["q1"][benefit_code_id] = round(
                    float(np.percentile(arr, 25, method="midpoint")), 2
                )
                stats["q2"][benefit_code_id] = round(
                    float(np.percentile(arr, 50, method="midpoint")), 2
                )
                stats["q3"][benefit_code_id] = round(
                    float(np.percentile(arr, 75, method="midpoint")), 2
                )
                stats["total"][benefit_code_id] = float(np.sum(arr))
        return stats
