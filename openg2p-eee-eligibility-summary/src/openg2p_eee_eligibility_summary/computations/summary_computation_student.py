from datetime import date
from typing import List

import numpy as np
from openg2p_eee_models.models import G2PEligibilitySummaryStudent
from openg2p_sr_models.models import G2PStudentRegistry
from sqlalchemy.orm import Session

from ..interface import SummaryComputationInterface


class SummaryComputationStudent(SummaryComputationInterface):
    """Fetches student data and computes summary statistics"""

    def get_summary(
        self, request_id: int, eee_session: Session
    ) -> G2PEligibilitySummaryStudent:
        return (
            eee_session.query(G2PEligibilitySummaryStudent)
            .filter(G2PEligibilitySummaryStudent.eligibility_request_id == request_id)
            .first()
        )

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

        student_summary = G2PEligibilitySummaryStudent(
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
