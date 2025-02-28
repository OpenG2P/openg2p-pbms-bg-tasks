from openg2p_sr_models.models import G2PRegistryType

from ..computations import (
    SummaryComputationFarmer,
    SummaryComputationStudent,
)
from ..interface import SummaryComputationInterface


class EligibilitySummaryFactory:
    """Get the appropriate summary computation class based on the registrant type"""

    @staticmethod
    def get_summary_computation_class(
        target_registry_type,
    ) -> SummaryComputationInterface:
        if target_registry_type == G2PRegistryType.FARMER.value:
            return SummaryComputationFarmer()

        elif target_registry_type == G2PRegistryType.STUDENT.value:
            return SummaryComputationStudent()

        else:
            raise ValueError(f"Invalid registrant type: {target_registry_type}")
