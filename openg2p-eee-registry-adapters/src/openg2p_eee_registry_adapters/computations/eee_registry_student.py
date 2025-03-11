from datetime import date
from typing import List

import numpy as np
from fastapi_cache.decorator import cache
from openg2p_eee_models.models import EEEDetails
from openg2p_eee_models.schemas import EEEBeneficiarySearchResponsePayload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ..cache import beneficiary_count_key_builder
from ..interface import EEERegistryInterface
from ..models import EligibilitySummaryStudent, G2PStudentRegistry
from ..schema import EligibilitySummaryStudentPayload, G2PStudentRegistryPayload


class EEERegistryStudent(EEERegistryInterface):
    """Fetches student data and computes summary statistics"""

    # ===================
    # Summary API Methods
    # ===================
    async def get_summary(
        self, request_id: int, eee_session: Session
    ) -> EligibilitySummaryStudentPayload:
        eligibility_summary_student = (
            (
                await eee_session.execute(
                    select(EligibilitySummaryStudent).where(
                        EligibilitySummaryStudent.eee_request_id == request_id
                    )
                )
            )
            .scalars()
            .first()
        )

        summary = EligibilitySummaryStudentPayload(
            id=eligibility_summary_student.id,
            program_id=eligibility_summary_student.program_id,
            program_mnemonic=eligibility_summary_student.program_mnemonic,
            target_registry_type=eligibility_summary_student.target_registry_type,
            eee_request_id=eligibility_summary_student.eee_request_id,
            number_of_registrants=eligibility_summary_student.number_of_registrants,
            date_created=eligibility_summary_student.date_created,
            age_mean=eligibility_summary_student.age_mean,
            age_quartile_25=eligibility_summary_student.age_quartile_25,
            age_quartile_50=eligibility_summary_student.age_quartile_50,
            age_quartile_75=eligibility_summary_student.age_quartile_75,
        )

        return summary

    # ==============================
    # Beneficiary Search API Methods
    # ==============================
    async def search_beneficiaries(
        self,
        eee_session: AsyncSession,
        sr_session: AsyncSession,
        eee_request_id: int,
        target_registry_type: str,
        search_query,
        page=1,
        page_size=10,
        order_by="id asc",
    ) -> EEEBeneficiarySearchResponsePayload:
        registrant_ids = await eee_session.execute(
            select(EEEDetails.registrant_id).where(
                EEEDetails.eee_request_id == eee_request_id
            )
        )
        registrant_ids = registrant_ids.scalars().all()

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
            sr_session, eee_request_id, registrant_ids, search_query
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
        eee_request_id: int,
        registrant_ids: List[int],
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

    # =====================
    # Celery Worker Methods
    # =====================
    def compute_and_persist_summary(
        self, registrant_ids, base_summary, sr_session: Session, eee_session: Session
    ):
        registrants = self.get_registrants(registrant_ids, sr_session)
        students_age = [
            self.calculate_age(student.date_of_birth)
            for student in registrants
            if student.date_of_birth
        ]

        student_summary = EligibilitySummaryStudent(
            program_id=base_summary.program_id,
            program_mnemonic=base_summary.program_mnemonic,
            target_registry_type=base_summary.target_registry_type,
            eee_request_id=base_summary.eee_request_id,
            number_of_registrants=base_summary.number_of_registrants,
            date_created=base_summary.date_created,
        )

        if students_age:
            students_age_array = np.array(students_age)
            # 25 percent of students are below this age
            student_summary.age_quartile_25 = float(
                np.percentile(students_age_array, 25, method="midpoint")
            )
            # 50 percent of students are below this age
            student_summary.age_quartile_50 = float(
                np.percentile(students_age_array, 50, method="midpoint")
            )
            # 75 percent of students are below this age
            student_summary.age_quartile_75 = float(
                np.percentile(students_age_array, 75, method="midpoint")
            )
            student_summary.age_mean = float(np.mean(students_age_array))

        eee_session.add(student_summary)

    def get_registrants(self, registrant_ids, sr_session) -> List[G2PStudentRegistry]:
        return (
            sr_session.query(G2PStudentRegistry)
            .filter(G2PStudentRegistry.id.in_(registrant_ids))
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
