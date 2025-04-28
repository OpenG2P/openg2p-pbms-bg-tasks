import json
from collections import defaultdict
from typing import List

import numpy as np
from fastapi_cache.decorator import cache
from openg2p_eee_models.models import EEEDetails
from openg2p_eee_models.schemas import (
    EEEBeneficiarySearchResponsePayload,
    RegistrantDetails,
)
from openg2p_pbms_models.models import Gender
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
        self, pbms_request_id: str, eee_session: AsyncSession, formated: bool = False
    ) -> EEESummaryFarmerPayload:
        eligibility_summary_farmer = await eee_session.execute(
            select(EEESummaryFarmer).where(
                EEESummaryFarmer.pbms_request_id == pbms_request_id
            )
        )
        eligibility_summary_farmer = eligibility_summary_farmer.scalars().first()

        number_of_registrants = eligibility_summary_farmer.number_of_registrants
        total_entitlement_amount = eligibility_summary_farmer.total_entitlement_amount
        average_entitlement_per_registrant = (
            eligibility_summary_farmer.average_entitlement_per_person
        )

        if formated:
            number_of_registrants = format(
                eligibility_summary_farmer.number_of_registrants, ","
            )
            total_entitlement_amount = (
                format(eligibility_summary_farmer.total_entitlement_amount, ",")
                + " "
                + eligibility_summary_farmer.entitlement_units
            )
            average_entitlement_per_registrant = (
                format(eligibility_summary_farmer.average_entitlement_per_person, ",")
                + " "
                + eligibility_summary_farmer.entitlement_units
            )

        summary = EEESummaryFarmerPayload(
            general_summary=EEEGeneralSummary(
                id=eligibility_summary_farmer.id,
                program_id=eligibility_summary_farmer.program_id,
                program_mnemonic=eligibility_summary_farmer.program_mnemonic,
                target_registry_type=eligibility_summary_farmer.target_registry_type,
                pbms_request_id=eligibility_summary_farmer.pbms_request_id,
                number_of_registrants=number_of_registrants,
                date_created=eligibility_summary_farmer.date_created,
                total_entitlement_amount=total_entitlement_amount,
                average_entitlement_per_registrant=average_entitlement_per_registrant,
            ),
            registry_summary=RegistrySummaryFarmerPayload(
                land_holding_mean=f"{eligibility_summary_farmer.land_holding_mean} {eligibility_summary_farmer.land_holding_units}",
                land_holding_quartile_25=f"{eligibility_summary_farmer.land_holding_quartile_25} {eligibility_summary_farmer.land_holding_units}",
                land_holding_quartile_50=f"{eligibility_summary_farmer.land_holding_quartile_50} {eligibility_summary_farmer.land_holding_units}",
                land_holding_quartile_75=f"{eligibility_summary_farmer.land_holding_quartile_75} {eligibility_summary_farmer.land_holding_units}",
                annual_income_mean=f"{eligibility_summary_farmer.annual_income_mean} {eligibility_summary_farmer.annual_income_units}",
                annual_income_quartile_25=f"{eligibility_summary_farmer.annual_income_quartile_25} {eligibility_summary_farmer.annual_income_units}",
                annual_income_quartile_50=f"{eligibility_summary_farmer.annual_income_quartile_50} {eligibility_summary_farmer.annual_income_units}",
                annual_income_quartile_75=f"{eligibility_summary_farmer.annual_income_quartile_75} {eligibility_summary_farmer.annual_income_units}",
                average_entitlement_female=f"{eligibility_summary_farmer.average_entitlement_female} {eligibility_summary_farmer.entitlement_units}",
                average_entitlement_male=f"{eligibility_summary_farmer.average_entitlement_male} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_75=f"{eligibility_summary_farmer.entitlement_amount_q3} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_50=f"{eligibility_summary_farmer.entitlement_amount_q2} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_25=f"{eligibility_summary_farmer.entitlement_amount_q1} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_male_75=f"{eligibility_summary_farmer.entitlement_amount_male_q3} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_male_50=f"{eligibility_summary_farmer.entitlement_amount_male_q2} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_male_25=f"{eligibility_summary_farmer.entitlement_amount_male_q1} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_female_75=f"{eligibility_summary_farmer.entitlement_amount_female_q3} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_female_50=f"{eligibility_summary_farmer.entitlement_amount_female_q2} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_female_25=f"{eligibility_summary_farmer.entitlement_amount_female_q1} {eligibility_summary_farmer.entitlement_units}",
            ),
        )

        return summary

    def get_summary_sync(
        self, pbms_request_id: str, eee_session: Session
    ) -> EEESummaryFarmerPayload:
        eligibility_summary_farmer = (
            eee_session.query(EEESummaryFarmer)
            .filter_by(pbms_request_id=pbms_request_id)
            .first()
        )

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
                land_holding_mean=f"{eligibility_summary_farmer.land_holding_mean} {eligibility_summary_farmer.land_holding_units}",
                land_holding_quartile_75=f"{eligibility_summary_farmer.land_holding_quartile_75} {eligibility_summary_farmer.land_holding_units}",
                land_holding_quartile_50=f"{eligibility_summary_farmer.land_holding_quartile_50} {eligibility_summary_farmer.land_holding_units}",
                land_holding_quartile_25=f"{eligibility_summary_farmer.land_holding_quartile_25} {eligibility_summary_farmer.land_holding_units}",
                annual_income_mean=f"{eligibility_summary_farmer.annual_income_mean} {eligibility_summary_farmer.annual_income_units}",
                annual_income_quartile_75=f"{eligibility_summary_farmer.annual_income_quartile_75} {eligibility_summary_farmer.annual_income_units}",
                annual_income_quartile_50=f"{eligibility_summary_farmer.annual_income_quartile_50} {eligibility_summary_farmer.annual_income_units}",
                annual_income_quartile_25=f"{eligibility_summary_farmer.annual_income_quartile_25} {eligibility_summary_farmer.annual_income_units}",
                average_entitlement_female=f"{eligibility_summary_farmer.average_entitlement_female} {eligibility_summary_farmer.entitlement_units}",
                average_entitlement_male=f"{eligibility_summary_farmer.average_entitlement_male} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_75=f"{eligibility_summary_farmer.entitlement_amount_q3} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_50=f"{eligibility_summary_farmer.entitlement_amount_q2} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_25=f"{eligibility_summary_farmer.entitlement_amount_q1} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_male_75=f"{eligibility_summary_farmer.entitlement_amount_male_q3} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_male_50=f"{eligibility_summary_farmer.entitlement_amount_male_q2} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_male_25=f"{eligibility_summary_farmer.entitlement_amount_male_q1} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_female_75=f"{eligibility_summary_farmer.entitlement_amount_female_q3} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_female_50=f"{eligibility_summary_farmer.entitlement_amount_female_q2} {eligibility_summary_farmer.entitlement_units}",
                entitlement_amount_female_25=f"{eligibility_summary_farmer.entitlement_amount_female_q1} {eligibility_summary_farmer.entitlement_units}",
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
        registrant_details = await eee_session.execute(
            select(EEEDetails.registrant_details).where(
                EEEDetails.pbms_request_id == pbms_request_id
            )
        )
        registrant_details = registrant_details.scalars().all()
        registrant_ids = []
        for registrant_detail in registrant_details:
            for registrant in registrant_detail:
                registrant_ids.append(registrant["registrant_id"])

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
        self,
        eee_details: List[dict],
        base_summary,
        sr_session: Session,
        eee_session: Session,
    ):
        farmer_summary = EEESummaryFarmer(
            program_id=base_summary.program_id,
            program_mnemonic=base_summary.program_mnemonic,
            target_registry_type=base_summary.target_registry_type,
            pbms_request_id=base_summary.pbms_request_id,
            number_of_registrants=base_summary.number_of_registrants,
            date_created=base_summary.date_created,
        )

        land_areas = []
        annual_incomes = []

        for eee_detail in eee_details:
            registrant_ids = []
            for registrant in json.loads(eee_detail["registrant_details"]):
                registrant_ids.append(registrant["registrant_id"])

            registrants = self.get_registrants_by_ids(registrant_ids, sr_session)
            for farmer in registrants:
                land_areas.append(farmer.land_area)
                annual_incomes.append(farmer.annual_income)

        # Land Area Summary
        if land_areas:
            land_areas_array = np.array(land_areas)
            farmer_summary.land_holding_mean = round(
                float(np.mean(land_areas_array)), 2
            )
            farmer_summary.land_holding_quartile_25 = round(
                float(np.percentile(land_areas_array, 25, method="midpoint")), 2
            )
            farmer_summary.land_holding_quartile_50 = round(
                float(np.percentile(land_areas_array, 50, method="midpoint")), 2
            )
            farmer_summary.land_holding_quartile_75 = round(
                float(np.percentile(land_areas_array, 75, method="midpoint")), 2
            )

        # Annual Income Summary
        if annual_incomes:
            annual_incomes_array = np.array(annual_incomes)
            farmer_summary.annual_income_mean = round(
                float(np.mean(annual_incomes_array)), 2
            )
            farmer_summary.annual_income_quartile_25 = round(
                float(np.percentile(annual_incomes_array, 25, method="midpoint")), 2
            )
            farmer_summary.annual_income_quartile_50 = round(
                float(np.percentile(annual_incomes_array, 50, method="midpoint")), 2
            )
            farmer_summary.annual_income_quartile_75 = round(
                float(np.percentile(annual_incomes_array, 75, method="midpoint")), 2
            )

        eee_session.add(farmer_summary)

    def get_registrants_by_ids(
        self, registrant_ids, sr_session
    ) -> List[G2PFarmerRegistry]:
        return (
            sr_session.query(G2PFarmerRegistry)
            .filter(G2PFarmerRegistry.unique_id.in_(registrant_ids))
            .all()
        )

    # =================================
    # Entitlement Celery Worker Methods
    # =================================
    def lock_and_update_summary(
        self, number_of_registrants: int, pbms_request_id: str, eee_session: Session
    ) -> None:
        try:
            summary_farmer = (
                eee_session.query(EEESummaryFarmer)
                .filter_by(pbms_request_id=pbms_request_id)
                .with_for_update()
                .one()
            )
            summary_farmer.number_of_entitlements_processed += number_of_registrants
            eee_session.commit()
        except Exception as _:
            eee_session.rollback()

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
        self, pbms_request_id: str, eee_session: Session, sr_session: Session
    ):
        summary_farmer = (
            eee_session.query(EEESummaryFarmer)
            .filter_by(pbms_request_id=pbms_request_id)
            .first()
        )

        if (
            summary_farmer.number_of_entitlements_processed
            != summary_farmer.number_of_registrants
        ):
            return

        eee_details = (
            eee_session.query(EEEDetails)
            .filter_by(pbms_request_id=pbms_request_id)
            .all()
        )

        registrant_map: dict[str, G2PFarmerRegistry] = defaultdict(list)

        for eee_detail in eee_details:
            registrant_ids = []
            for registrant_detail in eee_detail.registrant_details:
                registrant_detail = RegistrantDetails(**registrant_detail)
                registrant_ids.append(registrant_detail.registrant_id)

            registrants_list: List[G2PFarmerRegistry] = self.get_registrants_by_ids(
                registrant_ids, sr_session
            )

            for registrant in registrants_list:
                registrant_map[str(registrant.unique_id)] = registrant

        entitlements = []
        entitlements_male = []
        entitlements_female = []

        for eee_detail in eee_details:
            for registrant_detail in eee_detail.registrant_details:
                registrant_detail = RegistrantDetails(**registrant_detail)
                entitlements.append(registrant_detail.entitlement_quantity)

                registrant = registrant_map.get(str(registrant_detail.registrant_id))

                gender = registrant.gender if registrant else None

                if gender == Gender.MALE.value:
                    entitlements_male.append(registrant_detail.entitlement_quantity)
                elif gender == Gender.FEMALE.value:
                    entitlements_female.append(registrant_detail.entitlement_quantity)
                else:
                    raise ValueError(f"Invalid gender: {gender}")

        # Compute all summary stats
        entitlement_stats = self.compute_stats(entitlements)
        entitlement_male_stats = self.compute_stats(entitlements_male)
        entitlement_female_stats = self.compute_stats(entitlements_female)

        eee_session.execute(
            update(EEESummaryFarmer)
            .where(EEESummaryFarmer.pbms_request_id == pbms_request_id)
            .values(
                total_entitlement_amount=entitlement_stats["total"],
                average_entitlement_per_person=entitlement_stats["average"],
                entitlement_amount_q1=entitlement_stats["q1"],
                entitlement_amount_q2=entitlement_stats["q2"],
                entitlement_amount_q3=entitlement_stats["q3"],
                average_entitlement_male=entitlement_male_stats["average"],
                entitlement_amount_male_q1=entitlement_male_stats["q1"],
                entitlement_amount_male_q2=entitlement_male_stats["q2"],
                entitlement_amount_male_q3=entitlement_male_stats["q3"],
                average_entitlement_female=entitlement_female_stats["average"],
                entitlement_amount_female_q1=entitlement_female_stats["q1"],
                entitlement_amount_female_q2=entitlement_female_stats["q2"],
                entitlement_amount_female_q3=entitlement_female_stats["q3"],
            )
        )

    def compute_stats(self, input_list: List[float]) -> dict:
        if not input_list:
            return {"average": 0.0, "q1": 0.0, "q2": 0.0, "q3": 0.0, "total": 0.0}

        arr = np.array(input_list)
        return {
            "average": round(float(np.mean(arr)), 2),
            "q1": round(float(np.percentile(arr, 25, method="midpoint")), 2),
            "q2": round(float(np.percentile(arr, 50, method="midpoint")), 2),
            "q3": round(float(np.percentile(arr, 75, method="midpoint")), 2),
            "total": float(np.sum(arr)),
        }
