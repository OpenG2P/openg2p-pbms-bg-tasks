from typing import List, Dict

import numpy as np
from fastapi_cache.decorator import cache
from openg2p_bg_task_models.models import BeneficiaryListDetails
from openg2p_bg_task_models.schemas import (
    BeneficiarySearchResponsePayload,
    RegistrantDetails,
)
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ..cache import beneficiary_count_key_builder
from ..interface import RegistryInterface
from ..models import (
    BeneficiaryListSummaryWorker as BeneficiaryListSummaryWorkerModel,
    G2PWorkerRegistry,
)
from ..schema import (
    BeneficiaryListSummary,
    BeneficiaryListSummaryWorker,
    BeneficiaryListSummaryWorkerPayload,
    G2PWorkerRegistryPayload,
)


class RegistryWorker(RegistryInterface):
    """Fetches worker data and computes summary statistics"""

    # ===================
    # Summary API Methods
    # ===================
    async def get_summary(
        self,
        beneficiary_list_id: str,
        bg_task_session: AsyncSession,
        formated: bool = False,
    ) -> BeneficiaryListSummaryWorkerPayload:
        result = await bg_task_session.execute(
            select(BeneficiaryListSummaryWorkerModel).where(
                BeneficiaryListSummaryWorkerModel.beneficiary_list_id == beneficiary_list_id
            )
        )
        summary_worker = result.scalars().first()
        if not summary_worker:
            return None

        return BeneficiaryListSummaryWorkerPayload(
            beneficiary_list_summary=BeneficiaryListSummary(
                id=summary_worker.id,
                program_id=summary_worker.program_id,
                program_mnemonic=summary_worker.program_mnemonic,
                target_registry=summary_worker.target_registry,
                beneficiary_list_id=summary_worker.beneficiary_list_id,
                number_of_registrants=summary_worker.number_of_registrants,
                date_created=summary_worker.date_created,
                total_disbursement_quantity=summary_worker.total_disbursement_quantity,
                average_entitlement_per_registrant=summary_worker.average_entitlement_per_person,
            ),
            registry_summary=BeneficiaryListSummaryWorker(
                entitlement_amount_q3=summary_worker.entitlement_amount_q3,
                entitlement_amount_q2=summary_worker.entitlement_amount_q2,
                entitlement_amount_q1=summary_worker.entitlement_amount_q1,
            ),
        )

    def get_summary_sync(
        self, beneficiary_list_id: str, bg_task_session: Session
    ) -> BeneficiaryListSummaryWorkerPayload:
        summary_worker = (
            bg_task_session.query(BeneficiaryListSummaryWorkerModel)
            .filter_by(beneficiary_list_id=beneficiary_list_id)
            .first()
        )
        if not summary_worker:
            return None

        return BeneficiaryListSummaryWorkerPayload(
            beneficiary_list_summary=BeneficiaryListSummary(
                id=summary_worker.id,
                program_id=summary_worker.program_id,
                program_mnemonic=summary_worker.program_mnemonic,
                target_registry=summary_worker.target_registry,
                beneficiary_list_id=summary_worker.beneficiary_list_id,
                number_of_registrants=summary_worker.number_of_registrants,
                date_created=summary_worker.date_created,
                total_disbursement_quantity=summary_worker.total_disbursement_quantity,
                average_entitlement_per_registrant=summary_worker.average_entitlement_per_person,
            ),
            registry_summary=BeneficiaryListSummaryWorker(
                entitlement_amount_q3=summary_worker.entitlement_amount_q3,
                entitlement_amount_q2=summary_worker.entitlement_amount_q2,
                entitlement_amount_q1=summary_worker.entitlement_amount_q1,
            ),
        )

    # ==============================
    # Beneficiary Search API Methods
    # ==============================
    async def search_beneficiaries(
        self,
        bg_task_session: AsyncSession,
        sr_session: AsyncSession,
        beneficiary_list_id: str,
        target_registry: str,
        search_query,
        page=1,
        page_size=10,
        order_by="id asc",
    ) -> BeneficiarySearchResponsePayload:
        registrant_details_result = await bg_task_session.execute(
            select(BeneficiaryListDetails.registrant_details).where(
                BeneficiaryListDetails.beneficiary_list_id == beneficiary_list_id
            )
        )
        registrant_details = registrant_details_result.scalars().all()
        registrant_ids = [
            registrant["registrant_id"]
            for registrant_detail in registrant_details
            for registrant in registrant_detail
        ]

        worker_search_query, worker_search_params = self.construct_beneficiary_search_sql_query(
            registrant_ids, target_registry, search_query, order_by, page_size, page
        )
        worker_search_results = (
            (await sr_session.execute(worker_search_query, worker_search_params))
            .mappings()
            .all()
        )

        total_beneficiary_count: int = await self._get_total_beneficiary_count(
            sr_session, beneficiary_list_id, registrant_ids, search_query
        )
        beneficiaries = [
            G2PWorkerRegistryPayload(
                id=worker["id"],
                unique_id=worker["unique_id"],
                name=worker["name"],
                email=worker["email"],
                phone=worker["phone"],
                age_group=worker["age_group"],
                province_id=worker["province_id"],
                district_id=worker["district_id"],
                constituency_id=worker["constituency_id"],
                ward_id=worker["ward_id"],
            )
            for worker in worker_search_results
        ] if worker_search_results else []

        return BeneficiarySearchResponsePayload(
            total_beneficiary_count=total_beneficiary_count,
            page=page,
            page_size=page_size,
            beneficiaries=beneficiaries,
        )

    @cache(expire=120, key_builder=beneficiary_count_key_builder)
    async def _get_total_beneficiary_count(
        self,
        sr_session: AsyncSession,
        beneficiary_list_id: str,
        registrant_ids: List[str],
        search_query: str,
    ) -> int:
        beneficiary_count_query, beneficiary_count_params = self.construct_beneficiary_search_count_sql_query(
            registrant_ids, "worker", search_query
        )
        total_beneficiary_count = (
            await sr_session.execute(beneficiary_count_query, beneficiary_count_params)
        ).scalar_one()
        return total_beneficiary_count

    # =================================
    # Eligibility Celery Worker Methods
    # =================================
    def compute_eligibility_statistics(
        self,
        beneficiary_list_details: List[BeneficiaryListDetails],
        base_summary,
        sr_session: Session,
        bg_task_session: Session,
    ):
        worker_summary = BeneficiaryListSummaryWorkerModel(
            program_id=base_summary.program_id,
            program_mnemonic=base_summary.program_mnemonic,
            target_registry=base_summary.target_registry,
            beneficiary_list_id=base_summary.beneficiary_list_id,
            number_of_registrants=base_summary.number_of_registrants,
            date_created=base_summary.date_created,
        )

        for beneficiary_list_detail in beneficiary_list_details:
            registrant_ids = [
                RegistrantDetails(**registrant_detail).registrant_id
                for registrant_detail in beneficiary_list_detail.registrant_details
            ]
            registrants = self.get_registrants_by_ids(registrant_ids, sr_session)

        bg_task_session.add(worker_summary)

    def get_registrants_by_ids(
        self, registrant_ids: List[str], sr_session: Session
    ) -> List[G2PWorkerRegistry]:
        workers = sr_session.query(G2PWorkerRegistry).filter(
            G2PWorkerRegistry.unique_id.in_(registrant_ids)
        )
        return list(workers.yield_per(500))

    # =================================
    # Entitlement Celery Worker Methods
    # =================================
    def get_is_registant_entitled(
        self, registrant_id: str, sql_query: str, sr_session: Session
    ) -> bool:
        sql_query_with_registrant_id = self.construct_get_is_registrant_entitled_sql_query(
            registrant_id, "worker", sql_query
        )
        result = sr_session.execute(sql_query_with_registrant_id).fetchone()
        return result is not None

    def get_entitlement_multiplier(
        self, multiplier: str, registrant_id: str, sr_session: Session
    ) -> int:
        if not multiplier or multiplier == "none":
            return 1

        sql_query = self.construct_multiplier_sql_query(
            multiplier, target_registry="worker"
        )
        params = {"registrant_id": registrant_id}
        result = sr_session.execute(sql_query, params).fetchone()
        return int(result[0]) if result and result[0] is not None else 1

    def compute_entitlement_statistics(
        self, beneficiary_list_id: str, bg_task_session: Session, sr_session: Session
    ):
        beneficiary_list_details = (
            bg_task_session.query(BeneficiaryListDetails)
            .filter_by(beneficiary_list_id=beneficiary_list_id)
            .all()
        )

        registrant_map_from_registry: Dict[str, G2PWorkerRegistry] = {}

        for beneficiary_list_detail in beneficiary_list_details:
            registrant_ids = [
                RegistrantDetails(**registrant_detail).registrant_id
                for registrant_detail in beneficiary_list_detail.registrant_details
            ]
            registrants_list: List[G2PWorkerRegistry] = self.get_registrants_by_ids(
                registrant_ids, sr_session
            )
            for registrant in registrants_list:
                registrant_map_from_registry[str(registrant.unique_id)] = registrant

        entitlements: Dict[int, list[float]] = {}

        for beneficiary_list_detail in beneficiary_list_details:
            for registrant_detail in beneficiary_list_detail.registrant_details:
                registrant_detail_obj = RegistrantDetails(**registrant_detail)
                registrant = registrant_map_from_registry.get(
                    str(registrant_detail_obj.registrant_id)
                )
                gender = registrant.gender if registrant else None

                for benefit_code_id, value in registrant_detail_obj.entitlement.items():
                    entitlements.setdefault(benefit_code_id, []).append(value)

        entitlement_stats = self.compute_stats_dict(entitlements)

        bg_task_session.execute(
            update(BeneficiaryListSummaryWorkerModel)
            .where(
                BeneficiaryListSummaryWorkerModel.beneficiary_list_id == beneficiary_list_id
            )
            .values(
                total_disbursement_quantity=dict(entitlement_stats["total"]),
                average_entitlement_per_person=dict(entitlement_stats["average"]),
                entitlement_amount_q1=dict(entitlement_stats["q1"]),
                entitlement_amount_q2=dict(entitlement_stats["q2"]),
                entitlement_amount_q3=dict(entitlement_stats["q3"]),
            )
        )

    def compute_stats_dict(self, entitlements_dict: Dict[int, list[float]]) -> Dict[str, Dict[int, float]]:
        stats = {
            "average": {},
            "q1": {},
            "q2": {},
            "q3": {},
            "total": {},
        }
        for benefit_code_id, values in entitlements_dict.items():
            if not values:
                stats["average"][benefit_code_id] = 0.0
                stats["q1"][benefit_code_id] = 0.0
                stats["q2"][benefit_code_id] = 0.0
                stats["q3"][benefit_code_id] = 0.0
                stats["total"][benefit_code_id] = 0.0
            else:
                arr = np.array(values)
                stats["average"][benefit_code_id] = round(float(np.mean(arr)), 2)
                stats["q1"][benefit_code_id] = round(float(np.percentile(arr, 25, method="midpoint")), 2)
                stats["q2"][benefit_code_id] = round(float(np.percentile(arr, 50, method="midpoint")), 2)
                stats["q3"][benefit_code_id] = round(float(np.percentile(arr, 75, method="midpoint")), 2)
                stats["total"][benefit_code_id] = float(np.sum(arr))
        return stats
