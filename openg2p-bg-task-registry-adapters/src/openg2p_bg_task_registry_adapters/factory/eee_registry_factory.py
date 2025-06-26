from openg2p_bg_task_models.errors import EEEErrorCodes, EEEException

from ..computations import (
    EEERegistryFarmer,
    EEERegistryStudent,
)
from ..interface import EEERegistryInterface
from ..models import G2PRegistryType


class EEERegistryFactory:
    """Get the appropriate summary computation class based on the registrant type"""

    @staticmethod
    def get_registry_class(
        target_registry_type,
    ) -> EEERegistryInterface:
        if target_registry_type == G2PRegistryType.FARMER.value:
            return EEERegistryFarmer()

        elif target_registry_type == G2PRegistryType.STUDENT.value:
            return EEERegistryStudent()

        else:
            raise EEEException(code=EEEErrorCodes.INVALID_REQUEST)
