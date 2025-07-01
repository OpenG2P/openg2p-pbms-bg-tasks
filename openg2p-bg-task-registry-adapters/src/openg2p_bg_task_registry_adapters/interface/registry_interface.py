from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from openg2p_bg_task_models.schemas import (
    BeneficiarySearchResponsePayload,
    Disbursement,
)
from openg2p_pbms_models.models import G2PRegistry
from sqlalchemy import TextClause, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..schema import BeneficiaryListSummaryPayload


class RegistryInterface(ABC):
    """
    Base class for Registry Interface
    Defines methods for interacting with the registry classes
    """

    # ================
    # Summary methods
    # ================
    @abstractmethod
    async def get_summary(
        self, beneficiary_list_id: str, bg_task_session: Session, formated: bool = False
    ) -> BeneficiaryListSummaryPayload:
        # Abstract method to get summary statistics
        raise NotImplementedError("Subclasses must implement get_summary()")

    @abstractmethod
    def get_summary_sync(
        self, beneficiary_list_id: str, bg_task_session: Session
    ) -> BeneficiaryListSummaryPayload:
        # Abstract method to get summary statistics
        raise NotImplementedError("Subclasses must implement get_summary_sync()")

    @abstractmethod
    def compute_eligibility_statistics(
        self,
        beneficiary_list_details: List[dict],
        base_summary,
        sr_session: Session,
        bg_task_session: Session,
    ):
        # Abstract method to compute summary statistics
        raise NotImplementedError("Subclasses must implement compute_summary()")

    @abstractmethod
    def compute_entitlement_statistics(
        self, beneficiary_list_id: str, bg_task_session: Session, sr_session: Session
    ):
        # Abstract method to compute entitlements fields and modify summary
        raise NotImplementedError(
            "Subclasses must implement compute_entitlement_statistics()"
        )

    # =================
    # Registry methods
    # =================
    @abstractmethod
    def get_registrants_by_ids(self, registrant_ids) -> List[G2PRegistry]:
        # Abstract method to fetch registrants from the database using session
        raise NotImplementedError("Subclasses must implement get_registrants()")

    @abstractmethod
    def get_is_registant_entitled(
        self, registrant_id: str, sql_query: str, sr_session: Session
    ) -> bool:
        # Abstract method to check if registrant is entitled
        raise NotImplementedError(
            "Subclasses must implement get_is_registant_entitled()"
        )

    @abstractmethod
    def get_entitlement_multiplier(self, multiplier: str, sr_session: Session) -> int:
        # Abstract method to get the multiplier value for entitlement calculation
        raise NotImplementedError(
            "Subclasses must implement get_entitlement_multiplier()"
        )

    @abstractmethod
    async def search_beneficiaries(
        self,
        bg_task_session: AsyncSession,
        pbms_session: AsyncSession,
        beneficiary_list_id: str,
        target_registry: str,
        search_query: str,
        page: int,
        page_size: int,
        order_by: str,
    ) -> BeneficiarySearchResponsePayload:
        # Abstract method to search beneficiaries for particular eligibility request id
        raise NotImplementedError("Subclasses must implement search_beneficiaries()")

    def get_bridge_disbursement_details(
        self,
        beneficiary_list_id: str,
        registrant_ids: List[str],
        bg_task_session: Session,
    ) -> List[Disbursement]:
        sql_query = text("")

        disbursements = bg_task_session.execute(sql_query)

        return disbursements

    # ===============================
    # Registry SQL Query Constructors
    # ===============================
    def construct_multiplier_sql_query(
        self, multiplier: str, target_registry: str
    ) -> TextClause:
        if not multiplier or multiplier == "none":
            return None

        table_name = f"g2p_{target_registry}_registry"
        sql_query = text(
            f"""
            SELECT {multiplier} FROM {table_name}
            WHERE unique_id = :registrant_id
            """
        )
        return sql_query

    def construct_beneficiary_search_sql_query(
        self,
        registrant_ids: List[str],
        target_registry: str,
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

        table_name = f"g2p_{target_registry}_registry"
        where_clause_sql = f" AND {where_clause}" if where_clause else ""
        registrant_placeholders = ", ".join(
            [f":registrant_id_{i}" for i in range(len(registrant_ids))]
        )

        sql_query = text(
            f"""
            SELECT * FROM {table_name}
            WHERE unique_id IN ({registrant_placeholders}) {where_clause_sql}
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
        self, registrant_ids: List[str], target_registry: str, where_clause: str
    ) -> Tuple[TextClause, Dict[str, Any]]:
        if not registrant_ids:
            return None, {}

        # Replace curly quotes in the where clause
        where_clause = where_clause.replace("“", '"').replace("”", '"')
        where_clause = where_clause.replace("‘", "'").replace("’", "'")

        table_name = f"g2p_{target_registry}_registry"
        where_clause_sql = f" AND {where_clause}" if where_clause else ""
        registrant_placeholders = ", ".join(
            [f":registrant_id_{i}" for i in range(len(registrant_ids))]
        )

        sql_query = text(
            f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE unique_id IN ({registrant_placeholders}) {where_clause_sql}
        """
        )

        params = {
            f"registrant_id_{i}": registrant_ids[i] for i in range(len(registrant_ids))
        }

        return sql_query, params

    def construct_get_is_registrant_entitled_sql_query(
        self, registrant_id: str, target_registry: str, sql_query: str
    ) -> TextClause:
        sql_query = sql_query.strip()

        if not registrant_id:
            raise ValueError("registrant_id cannot be None or zero")
        if not sql_query.upper().startswith("SELECT"):
            raise ValueError("Invalid SQL query: Must be a valid SELECT statement")

        if "WHERE" in sql_query.upper():
            sql_query += (
                f" AND g2p_{target_registry}_registry.unique_id = :registrant_id"
            )
        else:
            sql_query += (
                f" WHERE g2p_{target_registry}_registry.unique_id = :registrant_id"
            )

        params = {"registrant_id": registrant_id}

        return text(sql_query).params(**params)
