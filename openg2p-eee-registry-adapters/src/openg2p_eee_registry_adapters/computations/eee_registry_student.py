import logging
from datetime import date
from typing import List

import numpy as np
from fastapi_cache.decorator import cache
from openg2p_eee_models.models import EEEDetails
from openg2p_eee_models.schemas import EEEBeneficiarySearchResponsePayload
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ..cache import beneficiary_count_key_builder
from ..interface import EEERegistryInterface
from ..models import EEESummaryStudent, G2PStudentRegistry
from ..schema import (
    EEEGeneralSummary,
    EEESummaryStudentPayload,
    G2PStudentRegistryPayload,
    RegistrySummaryStudentPayload,
)

_logger = logging.getLogger("openg2p_eee_registry_adapters")


class EEERegistryStudent(EEERegistryInterface):
    """Fetches student data and computes summary statistics"""

    # ===================
    # Summary API Methods
    # ===================
    async def get_summary(
        self, pbms_request_id: int, eee_session: AsyncSession
    ) -> EEESummaryStudentPayload:
        _logger.info(f"Fetching summary for pbms_request_id: {pbms_request_id}")
        _logger.info(f"Type of session: {(eee_session)}")
        eligibility_summary_student = await (
            eee_session.execute(
                select(EEESummaryStudent).where(
                    EEESummaryStudent.pbms_request_id == pbms_request_id
                )
            )
        )
        eligibility_summary_student = eligibility_summary_student.scalars().first()

        summary = EEESummaryStudentPayload(
            general_summary=EEEGeneralSummary(
                id=eligibility_summary_student.id,
                program_id=eligibility_summary_student.program_id,
                program_mnemonic=eligibility_summary_student.program_mnemonic,
                target_registry_type=eligibility_summary_student.target_registry_type,
                pbms_request_id=eligibility_summary_student.pbms_request_id,
                number_of_registrants=eligibility_summary_student.number_of_registrants,
                date_created=eligibility_summary_student.date_created,
                total_entitlement_amount=eligibility_summary_student.total_entitlement_amount,
                average_entitlement_per_registrant=eligibility_summary_student.average_entitlement_per_person,
            ),
            registry_summary=RegistrySummaryStudentPayload(
                age_mean=eligibility_summary_student.age_mean,
                age_quartile_25=eligibility_summary_student.age_quartile_25,
                age_quartile_50=eligibility_summary_student.age_quartile_50,
                age_quartile_75=eligibility_summary_student.age_quartile_75,
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
        eee_session: AsyncSession,
        sr_session: AsyncSession,
        pbms_request_id: str,
        target_registry_type: str,
        search_query,
        page=1,
        page_size=10,
        order_by="id asc",
    ) -> EEEBeneficiarySearchResponsePayload:
        registrant_ids = await eee_session.execute(
            select(EEEDetails.registrant_id).where(
                EEEDetails.pbms_request_id == pbms_request_id
            )
        )
        registrant_ids = registrant_ids.scalars().all()

        # TODO: Implement batching in beneficiary search
        (
            student_search_query,
            student_search_params,
        ) = self.construct_beneficiary_search_sql_query(
            registrant_ids,
            target_registry_type,
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
            sr_session, pbms_request_id, registrant_ids, search_query
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

        response_payload = EEEBeneficiarySearchResponsePayload(
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
        pbms_request_id: str,
        registrant_ids: List[str],
        search_query: str,
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
    def compute_and_persist_summary(
        self, registrant_ids, base_summary, sr_session: Session, eee_session: Session
    ):
        registrants = self.get_registrants(registrant_ids, sr_session)
        students_age = [
            self.calculate_age(student.date_of_birth)
            for student in registrants
            if student.date_of_birth
        ]

        student_summary = EEESummaryStudent(
            program_id=base_summary.program_id,
            program_mnemonic=base_summary.program_mnemonic,
            target_registry_type=base_summary.target_registry_type,
            pbms_request_id=base_summary.pbms_request_id,
            number_of_registrants=base_summary.number_of_registrants,
            date_created=base_summary.date_created,
        )

        if students_age:
            students_age_array = np.array(students_age)
            student_summary.age_quartile_25 = float(
                np.percentile(students_age_array, 25, method="midpoint")
            )
            student_summary.age_quartile_50 = float(
                np.percentile(students_age_array, 50, method="midpoint")
            )
            student_summary.age_quartile_75 = float(
                np.percentile(students_age_array, 75, method="midpoint")
            )
            student_summary.age_mean = float(np.mean(students_age_array))

        eee_session.add(student_summary)

    def get_registrants(self, registrant_ids, sr_session) -> List[G2PStudentRegistry]:
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

    def compute_entitlements_and_modify_summary(
        self, entitlements: List[float], pbms_request_id: str, eee_session: Session
    ):
        if not entitlements:
            return

        entitlement_values = np.array(entitlements)

        # Compute summary statistics
        total_entitlement_amount = float(np.sum(entitlement_values))
        average_entitlement_per_person = float(np.mean(entitlement_values))
        entitlement_amount_q1 = float(
            np.percentile(entitlement_values, 25, method="midpoint")
        )
        entitlement_amount_q2 = float(
            np.percentile(entitlement_values, 50, method="midpoint")
        )
        entitlement_amount_q3 = float(
            np.percentile(entitlement_values, 75, method="midpoint")
        )

        # Update g2p_eligibility_summary_farmer record
        eee_session.execute(
            update(EEESummaryStudent)
            .where(EEESummaryStudent.pbms_request_id == pbms_request_id)
            .values(
                total_entitlement_amount=total_entitlement_amount,
                average_entitlement_per_person=average_entitlement_per_person,
                entitlement_amount_q1=entitlement_amount_q1,
                entitlement_amount_q2=entitlement_amount_q2,
                entitlement_amount_q3=entitlement_amount_q3,
            )
        )
