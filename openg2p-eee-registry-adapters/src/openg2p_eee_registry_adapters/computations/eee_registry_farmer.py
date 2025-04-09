from typing import List

import numpy as np
from fastapi_cache.decorator import cache
from openg2p_eee_models.models import EEEDetails
from openg2p_eee_models.schemas import EEEBeneficiarySearchResponsePayload
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ..cache import beneficiary_count_key_builder
from ..interface import EEERegistryInterface
from ..models import EEESummaryFarmer, G2PFarmerRegistry
from ..schema import (
    EEEGeneralSummary,
    EEESummaryFarmerPayload,
    G2PFarmerRegistryPayload,
    RegistrySummaryFarmerPayload,
)


class EEERegistryFarmer(EEERegistryInterface):
    """Fetches farmer data and computes summary statistics"""

    # ===================
    # Summary API Methods
    # ===================
    async def get_summary(
        self, pbms_request_id: str, eee_session: AsyncSession
    ) -> EEESummaryFarmerPayload:
        eligibility_summary_farmer = await (
            eee_session.execute(
                select(EEESummaryFarmer).where(
                    EEESummaryFarmer.pbms_request_id == pbms_request_id
                )
            )
        )
        eligibility_summary_farmer = eligibility_summary_farmer.scalars().first()

        summary = EEESummaryFarmerPayload(
            general_summary=EEEGeneralSummary(
                id=eligibility_summary_farmer.id,
                program_id=eligibility_summary_farmer.program_id,
                program_mnemonic=eligibility_summary_farmer.program_mnemonic,
                target_registry_type=eligibility_summary_farmer.target_registry_type,
                pbms_request_id=eligibility_summary_farmer.pbms_request_id,
                number_of_registrants=eligibility_summary_farmer.number_of_registrants,
                date_created=eligibility_summary_farmer.date_created,
                total_entitlement_amount=eligibility_summary_farmer.total_entitlement_amount,
                average_entitlement_per_registrant=eligibility_summary_farmer.average_entitlement_per_person,
            ),
            registry_summary=RegistrySummaryFarmerPayload(
                land_holding_mean=eligibility_summary_farmer.land_holding_mean,
                land_holding_quartile_25=eligibility_summary_farmer.land_holding_quartile_25,
                land_holding_quartile_50=eligibility_summary_farmer.land_holding_quartile_50,
                land_holding_quartile_75=eligibility_summary_farmer.land_holding_quartile_75,
                annual_income_mean=eligibility_summary_farmer.annual_income_mean,
                annual_income_quartile_25=eligibility_summary_farmer.annual_income_quartile_25,
                annual_income_quartile_50=eligibility_summary_farmer.annual_income_quartile_50,
                annual_income_quartile_75=eligibility_summary_farmer.annual_income_quartile_75,
                average_entitlement_female=eligibility_summary_farmer.average_entitlement_female,
                average_entitlement_male=eligibility_summary_farmer.average_entitlement_male,
                entitlement_amount_q1=eligibility_summary_farmer.entitlement_amount_q1,
                entitlement_amount_q2=eligibility_summary_farmer.entitlement_amount_q2,
                entitlement_amount_q3=eligibility_summary_farmer.entitlement_amount_q3,
                entitlement_amount_male_q1=eligibility_summary_farmer.entitlement_amount_male_q1,
                entitlement_amount_male_q2=eligibility_summary_farmer.entitlement_amount_male_q2,
                entitlement_amount_male_q3=eligibility_summary_farmer.entitlement_amount_male_q3,
                entitlement_amount_female_q1=eligibility_summary_farmer.entitlement_amount_female_q1,
                entitlement_amount_female_q2=eligibility_summary_farmer.entitlement_amount_female_q2,
                entitlement_amount_female_q3=eligibility_summary_farmer.entitlement_amount_female_q3,
            ),
        )

        return summary

    # ==============================
    # Beneficiary Search API Methods
    # ==============================
    async def search_beneficiaries(
        self,
        eee_session: AsyncSession,
        sr_session: AsyncSession,
        pbms_request_id: str,
        target_registry_type: str,
        search_query,
        page=1,
        page_size=10,
        order_by="id asc",
    ) -> EEEBeneficiarySearchResponsePayload:
        registrant_ids = await (
            eee_session.execute(
                select(EEEDetails.registrant_id).where(
                    EEEDetails.pbms_request_id == pbms_request_id
                )
            )
        )
        registrant_ids: List[str] = registrant_ids.scalars().all()

        # TODO: Implement batching in beneficiary search
        (
            farmer_search_query,
            farmer_search_params,
        ) = self.construct_beneficiary_search_sql_query(
            registrant_ids,
            target_registry_type,
            search_query,
            order_by,
            page_size,
            page,
        )
        farmer_search_results = (
            (await sr_session.execute(farmer_search_query, farmer_search_params))
            .mappings()
            .all()
        )

        total_beneficiary_count: int = await self._get_total_beneficiary_count(
            sr_session, pbms_request_id, registrant_ids, search_query
        )

        beneficiaries = []
        if farmer_search_results:
            beneficiaries = [
                G2PFarmerRegistryPayload(
                    id=farmer["id"],
                    unique_id=farmer["unique_id"],
                    registration_date=farmer["registration_date"],
                    name=farmer["name"],
                    land_area=farmer["land_area"],
                    no_of_cattle_heads=farmer["no_of_cattle_heads"],
                    no_of_poultry_heads=farmer["no_of_poultry_heads"],
                )
                for farmer in farmer_search_results
            ]

        response_payload = EEEBeneficiarySearchResponsePayload(
            total_beneficiary_count=total_beneficiary_count,
            page=page,
            page_size=page_size,
            beneficiaries=beneficiaries,
        )

        return response_payload

    @cache(expire=120, key_builder=beneficiary_count_key_builder)
    async def _get_total_beneficiary_count(
        self,
        sr_session: AsyncSession,
        pbms_request_id: str,
        registrant_ids: List[str],
        search_query: str,
    ) -> int:
        print("")
        (
            beneficiary_count_query,
            beneficiary_count_params,
        ) = self.construct_beneficiary_search_count_sql_query(
            registrant_ids, "farmer", search_query
        )
        total_beneficiary_count = (
            await sr_session.execute(beneficiary_count_query, beneficiary_count_params)
        ).scalar_one()

        return total_beneficiary_count

    # =================================
    # Eligibility Celery Worker Methods
    # =================================
    def compute_and_persist_summary(
        self, registrant_ids, base_summary, sr_session: Session, eee_session: Session
    ):
        registrants = self.get_registrants(registrant_ids, sr_session)
        land_areas = [
            farmer.land_area for farmer in registrants if farmer.land_area is not None
        ]

        farmer_summary = EEESummaryFarmer(
            program_id=base_summary.program_id,
            program_mnemonic=base_summary.program_mnemonic,
            target_registry_type=base_summary.target_registry_type,
            pbms_request_id=base_summary.pbms_request_id,
            number_of_registrants=base_summary.number_of_registrants,
            date_created=base_summary.date_created,
        )

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

        eee_session.add(farmer_summary)

    def get_registrants(self, registrant_ids, sr_session) -> List[G2PFarmerRegistry]:
        return (
            sr_session.query(G2PFarmerRegistry)
            .filter(G2PFarmerRegistry.unique_id.in_(registrant_ids))
            .all()
        )

    # =================================
    # Entitlement Celery Worker Methods
    # =================================
    def get_is_registant_entitled(
        self, registrant_id: str, sql_query: str, sr_session: Session
    ) -> bool:
        sql_query_with_registrant_id = (
            self.construct_get_is_registrant_entitled_sql_query(
                registrant_id, "farmer", sql_query
            )
        )

        result = sr_session.execute(sql_query_with_registrant_id).fetchone()
        return result is not None

    def compute_entitlements_and_modify_summary(
        self, entitlements: List[float], pbms_request_id: str, eee_session: Session
    ):
        if not entitlements:
            return

        entitlement_values = np.array(entitlements)

        # Compute summary statistics
        total_entitlement_amount = float(np.sum(entitlement_values))
        average_entitlement_per_person = float(np.mean(entitlement_values))
        entitlement_amount_q1 = float(
            np.percentile(entitlement_values, 25, method="midpoint")
        )
        entitlement_amount_q2 = float(
            np.percentile(entitlement_values, 50, method="midpoint")
        )
        entitlement_amount_q3 = float(
            np.percentile(entitlement_values, 75, method="midpoint")
        )

        # Update g2p_eligibility_summary_farmer record
        eee_session.execute(
            update(EEESummaryFarmer)
            .where(EEESummaryFarmer.pbms_request_id == pbms_request_id)
            .values(
                total_entitlement_amount=total_entitlement_amount,
                average_entitlement_per_person=average_entitlement_per_person,
                entitlement_amount_q1=entitlement_amount_q1,
                entitlement_amount_q2=entitlement_amount_q2,
                entitlement_amount_q3=entitlement_amount_q3,
            )
        )
