from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from openg2p_eee_models.schemas import EEEBeneficiarySearchResponsePayload
from openg2p_pbms_models.models import G2PRegistry
from sqlalchemy import TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..schema import EligibilitySummaryPayload


class EEERegistryInterface(ABC):
    """
    Base class for EEE Registry Interface
    Defines methods for interacting with the EEE registry classes
    """

    @abstractmethod
    async def get_summary(
        self, request_id: int, eee_session: Session
    ) -> EligibilitySummaryPayload:
        # Abstract method to get summary statistics
        raise NotImplementedError("Subclasses must implement get_summary()")

    @abstractmethod
    def get_registrants(self, registrant_ids) -> List[G2PRegistry]:
        # Abstract method to fetch registrants from the database using session
        raise NotImplementedError("Subclasses must implement get_registrants()")

    @abstractmethod
    async def search_beneficiaries(
        self,
        eee_session: AsyncSession,
        pbms_session: AsyncSession,
        eee_request_id: int,
        target_registry_type: str,
        search_query: str,
        page: int,
        page_size: int,
        order_by: str,
    ) -> EEEBeneficiarySearchResponsePayload:
        # Abstract method to search beneficiaries for particular eligibility request id
        raise NotImplementedError("Subclasses must implement search_beneficiaries()")

    @abstractmethod
    def compute_and_persist_summary(
        self, base_summary, sr_session: Session, eee_session: Session
    ):
        # Abstract method to compute summary statistics
        raise NotImplementedError("Subclasses must implement compute_summary()")

    # ======================
    # SQL Query Constructors
    # ======================
    def construct_beneficiary_search_sql_query(
        self,
        registrant_ids: List[int],
        target_registry_type: str,
        where_clause: str,
        order_by: str,
        page_size: int,
        page: int,
    ) -> Tuple[TextClause, Dict[str, Any]]:
        if not registrant_ids:
            return None, {}

        # Replace curly quotes in the where clause
        where_clause = where_clause.replace("“", '"').replace("”", '"')
        where_clause = where_clause.replace("‘", "'").replace("’", "'")

        table_name = f"g2p_{target_registry_type}_registry"
        where_clause_sql = f" AND {where_clause}" if where_clause else ""
        registrant_placeholders = ", ".join(
            [f":registrant_id_{i}" for i in range(len(registrant_ids))]
        )

        sql_query = text(
            f"""
            SELECT * FROM {table_name}
            WHERE id IN ({registrant_placeholders}) {where_clause_sql}
            ORDER BY {order_by}
            OFFSET :offset
            LIMIT :limit
        """
        )

        params = {
            f"registrant_id_{i}": registrant_ids[i] for i in range(len(registrant_ids))
        }
        params.update({"offset": page_size * (page - 1), "limit": page_size})

        return sql_query, params

    def construct_beneficiary_search_count_sql_query(
        self, registrant_ids: List[int], target_registry_type: str, where_clause: str
    ) -> Tuple[TextClause, Dict[str, Any]]:
        if not registrant_ids:
            return None, {}

        # Replace curly quotes in the where clause
        where_clause = where_clause.replace("“", '"').replace("”", '"')
        where_clause = where_clause.replace("‘", "'").replace("’", "'")

        table_name = f"g2p_{target_registry_type}_registry"
        where_clause_sql = f" AND {where_clause}" if where_clause else ""
        registrant_placeholders = ", ".join(
            [f":registrant_id_{i}" for i in range(len(registrant_ids))]
        )

        sql_query = text(
            f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE id IN ({registrant_placeholders}) {where_clause_sql}
        """
        )

        params = {
            f"registrant_id_{i}": registrant_ids[i] for i in range(len(registrant_ids))
        }

        return sql_query, params
