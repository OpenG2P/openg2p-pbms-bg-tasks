from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.orm import Session

from ..schema import G2PRegistry


class SummaryComputationInterface(ABC):
    """Interface for computing summary statistics"""

    @abstractmethod
    def get_summary(self, request_id: int, eee_session: Session):
        # Abstract method to get summary statistics
        raise NotImplementedError("Subclasses must implement get_summary()")

    @abstractmethod
    def get_registrants(self, registrant_ids) -> List[G2PRegistry]:
        # Abstract method to fetch registrants from the database using session
        raise NotImplementedError("Subclasses must implement get_registrants()")

    @abstractmethod
    def compute_and_persist_summary(
        self, base_summary, sr_session: Session, eee_session: Session
    ):
        # Abstract method to compute summary statistics
        raise NotImplementedError("Subclasses must implement compute_summary()")
