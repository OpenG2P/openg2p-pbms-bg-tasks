from datetime import date
from typing import List

import numpy as np
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from openg2p_eee_registry_adapters.models import EligibilitySummaryStudent

from ..interface import EEERegistryInterface
from ..models import G2PStudentRegistry
from ..schema import EligibilitySummaryStudentResponse


class EEERegistryStudent(EEERegistryInterface):
    """Fetches student data and computes summary statistics"""

    async def get_summary(
        self, request_id: int, eee_session: Session
    ) -> EligibilitySummaryStudentResponse:
        eligibility_summary_student = (
            (
                await eee_session.execute(
                    select(EligibilitySummaryStudent).where(
                        EligibilitySummaryStudent.eligibility_request_id == request_id
                    )
                )
            )
            .scalars()
            .first()
        )

        summary = EligibilitySummaryStudentResponse(
            id=eligibility_summary_student.id,
            program_id=eligibility_summary_student.program_id,
            program_mnemonic=eligibility_summary_student.program_mnemonic,
            target_registry_type=eligibility_summary_student.target_registry_type,
            eligibility_request_id=eligibility_summary_student.eligibility_request_id,
            number_of_registrants=eligibility_summary_student.number_of_registrants,
            date_created=eligibility_summary_student.date_created,
            age_mean=eligibility_summary_student.age_mean,
            age_quartile_25=eligibility_summary_student.age_quartile_25,
            age_quartile_50=eligibility_summary_student.age_quartile_50,
            age_quartile_75=eligibility_summary_student.age_quartile_75,
        )

        return summary

    def get_registrants(self, registrant_ids, sr_session) -> List[G2PStudentRegistry]:
        return (
            sr_session.query(G2PStudentRegistry)
            .filter(G2PStudentRegistry.id.in_(registrant_ids))
            .all()
        )

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
            eligibility_request_id=base_summary.eligibility_request_id,
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

    @staticmethod
    def calculate_age(birth_date) -> int:
        today = date.today()
        return (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )
