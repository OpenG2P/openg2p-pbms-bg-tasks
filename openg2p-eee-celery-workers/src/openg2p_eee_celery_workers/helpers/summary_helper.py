from datetime import date

import numpy as np
from openg2p_eee_models.models import (
    G2PEligibilitySummaryFarmer,
    G2PEligibilitySummaryStudent,
)


def construct_farmer_summary_statistics(base_summary, registrant_data):
    """
    Constructs summary statistics for farmers using numpy library
    """
    land_areas = [
        farmer.land_area for farmer in registrant_data if farmer.land_area is not None
    ]

    farmer_summary = G2PEligibilitySummaryFarmer(
        program_id=base_summary["program_id"],
        program_mnemonic=base_summary["program_mnemonic"],
        target_registry_type=base_summary["target_registry_type"],
        eligibility_request_id=base_summary["eligibility_request_id"],
        number_of_registrants=base_summary["number_of_registrants"],
        date_created=base_summary["date_created"],
    )

    # Calculate statistics if land_areas is not empty
    if land_areas:
        land_areas_array = np.array(land_areas)

        farmer_summary.land_holding_mean = float(np.mean(land_areas_array))
        farmer_summary.land_holding_quartile_25 = float(
            np.percentile(land_areas_array, 25, method="midpoint")
        )
        farmer_summary.land_holding_quartile_50 = float(
            np.percentile(land_areas_array, 50, method="midpoint")
        )
        farmer_summary.land_holding_quartile_75 = float(
            np.percentile(land_areas_array, 75, method="midpoint")
        )

    return farmer_summary


def construct_student_summary_statistics(base_summary, registrant_data):
    """
    Constructs summary statistics for students using numpy library
    """
    students_age = [
        calculate_age(student.date_of_birth)
        for student in registrant_data
        if student.date_of_birth is not None
    ]

    student_summary = G2PEligibilitySummaryStudent(
        program_id=base_summary["program_id"],
        program_mnemonic=base_summary["program_mnemonic"],
        target_registry_type=base_summary["target_registry_type"],
        eligibility_request_id=base_summary["eligibility_request_id"],
        number_of_registrants=base_summary["number_of_registrants"],
        date_created=base_summary["date_created"],
    )

    # Calculate statistics if we have age data
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

    return student_summary


def calculate_age(birth_date):
    if birth_date is None:
        return None
    today = date.today()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
