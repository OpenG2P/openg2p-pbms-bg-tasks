from sqlalchemy.orm import Session

from ..interface import RegistryInterface


class RegistryWorkerMonthly(RegistryInterface):
    async def get_summary(
        self, beneficiary_list_id: str, bg_task_session: Session, formated: bool = False
    ):
        return await super().get_summary(beneficiary_list_id, bg_task_session, formated)

    def get_summary_sync(
        self, beneficiary_list_id: str, bg_task_session: Session
    ):
        return super().get_summary_sync(beneficiary_list_id, bg_task_session)

    def compute_eligibility_statistics(
        self,
        beneficiary_list_details,
        base_summary,
        sr_session,
        bg_task_session,
    ):
        return super().compute_eligibility_statistics(
            beneficiary_list_details, base_summary, sr_session, bg_task_session
        )

    def compute_entitlement_statistics(
        self, beneficiary_list_id: str, bg_task_session: Session, sr_session: Session
    ):
        return super().compute_entitlement_statistics(
            beneficiary_list_id, bg_task_session, sr_session
        )

    def get_registrants_by_ids(self, registrant_ids):
        return super().get_registrants_by_ids(registrant_ids)

    async def search_beneficiaries(
        self,
        bg_task_session,
        pbms_session,
        beneficiary_list_id,
        target_registry,
        search_query,
        page,
        page_size,
        order_by,
    ):
        return await super().search_beneficiaries(
            bg_task_session,
            pbms_session,
            beneficiary_list_id,
            target_registry,
            search_query,
            page,
            page_size,
            order_by,
        )

    # =================================
    # Entitlement Celery Worker Methods
    # =================================
    def get_is_registant_entitled(
        self, registrant_id: str, sql_query: str, sr_session: Session
    ) -> bool:
        sql_query_with_registrant_id = self.construct_get_is_registrant_entitled_sql_query(
            registrant_id, "worker_monthly", sql_query
        )
        result = sr_session.execute(sql_query_with_registrant_id).fetchone()
        return result is not None

    def get_entitlement_multiplier(
        self, multiplier: str, registrant_id: str, sr_session: Session
    ) -> int:
        if not multiplier or multiplier == "none":
            return 1

        sql_query = self.construct_multiplier_sql_query(
            multiplier, target_registry="worker_monthly"
        )
        params = {"registrant_id": registrant_id}
        result = sr_session.execute(sql_query, params).fetchone()
        return int(result[0]) if result and result[0] is not None else 1
