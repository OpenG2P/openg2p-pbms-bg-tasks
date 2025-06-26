import json
from typing import List

import numpy as np
from fastapi_cache.decorator import cache
from openg2p_bg_task_models.models import BeneficiaryListDetails
from openg2p_bg_task_models.schemas import (
    BeneficiarySearchResponsePayload,
    RegistrantDetails,
)
from openg2p_pbms_models.models import Gender
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ..cache import beneficiary_count_key_builder
from ..interface import RegistryInterface
from ..models import BeneficiaryListSummaryFarmer, G2PFarmerRegistry
from ..schema import (
    G2PFarmerRegistryPayload,
    GeneralSummary,
    RegistrySummaryFarmerPayload,
    SummaryFarmerPayload,
)


class RegistryFarmer(RegistryInterface):
    """Fetches farmer data and computes summary statistics"""

    # ===================
    # Summary API Methods
    # ===================
    async def get_summary(
        self,
        beneficiary_list_id: str,
        bg_task_session: AsyncSession,
        formated: bool = False,
    ) -> SummaryFarmerPayload:
        beneficiary_list_summary_farmer = await bg_task_session.execute(
            select(BeneficiaryListSummaryFarmer).where(
                BeneficiaryListSummaryFarmer.beneficiary_list_id == beneficiary_list_id
            )
        )
        beneficiary_list_summary_farmer = (
            beneficiary_list_summary_farmer.scalars().first()
        )

        number_of_registrants = beneficiary_list_summary_farmer.number_of_registrants
        total_entitlement_amount = (
            beneficiary_list_summary_farmer.total_entitlement_amount
        )
        average_entitlement_per_registrant = (
            beneficiary_list_summary_farmer.average_entitlement_per_person
        )

        # if formated:
        #     number_of_registrants = format(
        #         beneficiary_list_summary_farmer.number_of_registrants, ","
        #     )
        #     total_entitlement_amount = (
        #         format(beneficiary_list_summary_farmer.total_entitlement_amount, ",")
        #         + " "
        #         + beneficiary_list_summary_farmer.entitlement_units
        #     )
        #     average_entitlement_per_registrant = (
        #         format(beneficiary_list_summary_farmer.average_entitlement_per_person, ",")
        #         + " "
        #         + beneficiary_list_summary_farmer.entitlement_units
        #     )

        summary_farmer_payload = SummaryFarmerPayload(
            general_summary=GeneralSummary(
                id=beneficiary_list_summary_farmer.id,
                program_id=beneficiary_list_summary_farmer.program_id,
                program_mnemonic=beneficiary_list_summary_farmer.program_mnemonic,
                target_registry=beneficiary_list_summary_farmer.target_registry,
                beneficiary_list_id=beneficiary_list_summary_farmer.beneficiary_list_id,
                number_of_registrants=number_of_registrants,
                date_created=beneficiary_list_summary_farmer.date_created,
                total_entitlement_amount=total_entitlement_amount,
                average_entitlement_per_registrant=average_entitlement_per_registrant,
            ),
            registry_summary=RegistrySummaryFarmerPayload(
                land_holding_mean=f"{beneficiary_list_summary_farmer.land_holding_mean} {beneficiary_list_summary_farmer.land_holding_units}",
                land_holding_quartile_25=f"{beneficiary_list_summary_farmer.land_holding_quartile_25} {beneficiary_list_summary_farmer.land_holding_units}",
                land_holding_quartile_50=f"{beneficiary_list_summary_farmer.land_holding_quartile_50} {beneficiary_list_summary_farmer.land_holding_units}",
                land_holding_quartile_75=f"{beneficiary_list_summary_farmer.land_holding_quartile_75} {beneficiary_list_summary_farmer.land_holding_units}",
                annual_income_mean=f"{beneficiary_list_summary_farmer.annual_income_mean} {beneficiary_list_summary_farmer.annual_income_units}",
                annual_income_quartile_25=f"{beneficiary_list_summary_farmer.annual_income_quartile_25} {beneficiary_list_summary_farmer.annual_income_units}",
                annual_income_quartile_50=f"{beneficiary_list_summary_farmer.annual_income_quartile_50} {beneficiary_list_summary_farmer.annual_income_units}",
                annual_income_quartile_75=f"{beneficiary_list_summary_farmer.annual_income_quartile_75} {beneficiary_list_summary_farmer.annual_income_units}",
                average_entitlement_female=beneficiary_list_summary_farmer.average_entitlement_female,
                average_entitlement_male=beneficiary_list_summary_farmer.average_entitlement_male,
                entitlement_amount_75=beneficiary_list_summary_farmer.entitlement_amount_q3,
                entitlement_amount_50=beneficiary_list_summary_farmer.entitlement_amount_q2,
                entitlement_amount_25=beneficiary_list_summary_farmer.entitlement_amount_q1,
                entitlement_amount_male_75=beneficiary_list_summary_farmer.entitlement_amount_male_q3,
                entitlement_amount_male_50=beneficiary_list_summary_farmer.entitlement_amount_male_q2,
                entitlement_amount_male_25=beneficiary_list_summary_farmer.entitlement_amount_male_q1,
                entitlement_amount_female_75=beneficiary_list_summary_farmer.entitlement_amount_female_q3,
                entitlement_amount_female_50=beneficiary_list_summary_farmer.entitlement_amount_female_q2,
                entitlement_amount_female_25=beneficiary_list_summary_farmer.entitlement_amount_female_q1,
            ),
        )

        return summary_farmer_payload

    def get_summary_sync(
        self, beneficiary_list_id: str, bg_task_session: Session
    ) -> SummaryFarmerPayload:
        beneficiary_list_summary_farmer = (
            bg_task_session.query(BeneficiaryListSummaryFarmer)
            .filter_by(beneficiary_list_id=beneficiary_list_id)
            .first()
        )

        summary_farmer_payload = SummaryFarmerPayload(
            general_summary=GeneralSummary(
                id=beneficiary_list_summary_farmer.id,
                program_id=beneficiary_list_summary_farmer.program_id,
                program_mnemonic=beneficiary_list_summary_farmer.program_mnemonic,
                target_registry=beneficiary_list_summary_farmer.target_registry,
                beneficiary_list_id=beneficiary_list_summary_farmer.beneficiary_list_id,
                number_of_registrants=beneficiary_list_summary_farmer.number_of_registrants,
                date_created=beneficiary_list_summary_farmer.date_created,
                total_entitlement_amount=beneficiary_list_summary_farmer.total_entitlement_amount,
                average_entitlement_per_registrant=beneficiary_list_summary_farmer.average_entitlement_per_person,
            ),
            registry_summary=RegistrySummaryFarmerPayload(
                land_holding_mean=f"{beneficiary_list_summary_farmer.land_holding_mean} {beneficiary_list_summary_farmer.land_holding_units}",
                land_holding_quartile_75=f"{beneficiary_list_summary_farmer.land_holding_quartile_75} {beneficiary_list_summary_farmer.land_holding_units}",
                land_holding_quartile_50=f"{beneficiary_list_summary_farmer.land_holding_quartile_50} {beneficiary_list_summary_farmer.land_holding_units}",
                land_holding_quartile_25=f"{beneficiary_list_summary_farmer.land_holding_quartile_25} {beneficiary_list_summary_farmer.land_holding_units}",
                annual_income_mean=f"{beneficiary_list_summary_farmer.annual_income_mean} {beneficiary_list_summary_farmer.annual_income_units}",
                annual_income_quartile_75=f"{beneficiary_list_summary_farmer.annual_income_quartile_75} {beneficiary_list_summary_farmer.annual_income_units}",
                annual_income_quartile_50=f"{beneficiary_list_summary_farmer.annual_income_quartile_50} {beneficiary_list_summary_farmer.annual_income_units}",
                annual_income_quartile_25=f"{beneficiary_list_summary_farmer.annual_income_quartile_25} {beneficiary_list_summary_farmer.annual_income_units}",
                average_entitlement_female=beneficiary_list_summary_farmer.average_entitlement_female,
                average_entitlement_male=beneficiary_list_summary_farmer.average_entitlement_male,
                entitlement_amount_75=beneficiary_list_summary_farmer.entitlement_amount_q3,
                entitlement_amount_50=beneficiary_list_summary_farmer.entitlement_amount_q2,
                entitlement_amount_25=beneficiary_list_summary_farmer.entitlement_amount_q1,
                entitlement_amount_male_75=beneficiary_list_summary_farmer.entitlement_amount_male_q3,
                entitlement_amount_male_50=beneficiary_list_summary_farmer.entitlement_amount_male_q2,
                entitlement_amount_male_25=beneficiary_list_summary_farmer.entitlement_amount_male_q1,
                entitlement_amount_female_75=beneficiary_list_summary_farmer.entitlement_amount_female_q3,
                entitlement_amount_female_50=beneficiary_list_summary_farmer.entitlement_amount_female_q2,
                entitlement_amount_female_25=beneficiary_list_summary_farmer.entitlement_amount_female_q1,
            ),
        )
        return summary_farmer_payload

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
        registrant_details = await bg_task_session.execute(
            select(BeneficiaryListDetails.registrant_details).where(
                BeneficiaryListDetails.beneficiary_list_id == beneficiary_list_id
            )
        )
        registrant_details = registrant_details.scalars().all()
        registrant_ids = []
        for registrant_detail in registrant_details:
            for registrant in registrant_detail:
                registrant_ids.append(registrant["registrant_id"])

        (
            farmer_search_query,
            farmer_search_params,
        ) = self.construct_beneficiary_search_sql_query(
            registrant_ids,
            target_registry,
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
            sr_session, beneficiary_list_id, registrant_ids, search_query
        )
        # TODO: get list_status from PBMS

        # TODO: unique_id -> registrant_id
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
        # if list_status == "approved_for_disbursement":
        #     disbursements = self.get_bridge_disbursement_details()

        response_payload = BeneficiarySearchResponsePayload(
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
        beneficiary_list_id: str,
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
        beneficiary_list_details: List[BeneficiaryListDetails],
        base_summary,
        sr_session: Session,
        bg_task_session: Session,
    ):
        farmer_summary = BeneficiaryListSummaryFarmer(
            program_id=base_summary.program_id,
            program_mnemonic=base_summary.program_mnemonic,
            target_registry=base_summary.target_registry,
            beneficiary_list_id=base_summary.beneficiary_list_id,
            number_of_registrants=base_summary.number_of_registrants,
            date_created=base_summary.date_created,
        )

        land_areas = []
        annual_incomes = []

        for beneficiary_list_detail in beneficiary_list_details:
            registrant_ids = []
            for registrant in json.loads(beneficiary_list_detail.registrant_details):
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

        bg_task_session.add(farmer_summary)

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
        self,
        number_of_registrants: int,
        beneficiary_list_id: str,
        bg_task_session: Session,
    ) -> None:
        try:
            summary_farmer = (
                bg_task_session.query(BeneficiaryListSummaryFarmer)
                .filter_by(beneficiary_list_id=beneficiary_list_id)
                .with_for_update()
                .one()
            )
            summary_farmer.number_of_entitlements_processed += number_of_registrants
            bg_task_session.commit()
        except Exception as _:
            bg_task_session.rollback()

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

    def get_entitlement_multiplier(
        self, multiplier: str, registrant_id: str, sr_session: Session
    ) -> int:
        if not multiplier or multiplier == "none":
            return 1

        sql_query = self.construct_multiplier_sql_query(
            multiplier, target_registry="farmer"
        )
        params = {"registrant_id": registrant_id}
        result = sr_session.execute(sql_query, params).fetchone()
        multiplier_value: int = (
            int(result[0]) if result and result[0] is not None else 1
        )

        return multiplier_value

    def compute_entitlements_and_modify_summary(
        self, beneficiary_list_id: str, bg_task_session: Session, sr_session: Session
    ):
        summary_farmer = (
            bg_task_session.query(BeneficiaryListSummaryFarmer)
            .filter_by(beneficiary_list_id=beneficiary_list_id)
            .first()
        )

        if (
            summary_farmer.number_of_entitlements_processed
            != summary_farmer.number_of_registrants
        ):
            return

        beneficiary_list_details = (
            bg_task_session.query(BeneficiaryListDetails)
            .filter_by(beneficiary_list_id=beneficiary_list_id)
            .all()
        )

        registrant_map: dict[str, G2PFarmerRegistry] = {}

        for beneficiary_list_detail in beneficiary_list_details:
            registrant_ids = []
            for registrant_detail in beneficiary_list_detail.registrant_details:
                registrant_detail = RegistrantDetails(**registrant_detail)
                registrant_ids.append(registrant_detail.registrant_id)

            registrants_list: List[G2PFarmerRegistry] = self.get_registrants_by_ids(
                registrant_ids, sr_session
            )

            for registrant in registrants_list:
                registrant_map[str(registrant.unique_id)] = registrant

        # Collect entitlements per benefit_code_id
        entitlements: dict[int, list[float]] = {}
        entitlements_male: dict[int, list[float]] = {}
        entitlements_female: dict[int, list[float]] = {}

        for beneficiary_list_detail in beneficiary_list_details:
            for registrant_detail in beneficiary_list_detail.registrant_details:
                registrant_detail = RegistrantDetails(**registrant_detail)
                registrant = registrant_map.get(str(registrant_detail.registrant_id))
                gender = registrant.gender if registrant else None

                for benefit_code_id, value in registrant_detail.entitlement.items():
                    # All entitlements
                    entitlements.setdefault(benefit_code_id, []).append(value)
                    # By gender
                    if gender == Gender.MALE.value:
                        entitlements_male.setdefault(benefit_code_id, []).append(value)
                    elif gender == Gender.FEMALE.value:
                        entitlements_female.setdefault(benefit_code_id, []).append(
                            value
                        )
                    else:
                        raise ValueError(f"Invalid gender: {gender}")

        # Compute all summary stats per benefit_code_id
        entitlement_stats = self.compute_stats_dict(entitlements)
        entitlement_male_stats = self.compute_stats_dict(entitlements_male)
        entitlement_female_stats = self.compute_stats_dict(entitlements_female)

        bg_task_session.execute(
            update(BeneficiaryListSummaryFarmer)
            .where(
                BeneficiaryListSummaryFarmer.beneficiary_list_id == beneficiary_list_id
            )
            .values(
                total_entitlement_amount=dict(entitlement_stats["total"]),
                average_entitlement_per_person=dict(entitlement_stats["average"]),
                entitlement_amount_q1=dict(entitlement_stats["q1"]),
                entitlement_amount_q2=dict(entitlement_stats["q2"]),
                entitlement_amount_q3=dict(entitlement_stats["q3"]),
                average_entitlement_male=dict(entitlement_male_stats["average"]),
                entitlement_amount_male_q1=dict(entitlement_male_stats["q1"]),
                entitlement_amount_male_q2=dict(entitlement_male_stats["q2"]),
                entitlement_amount_male_q3=dict(entitlement_male_stats["q3"]),
                average_entitlement_female=dict(entitlement_female_stats["average"]),
                entitlement_amount_female_q1=dict(entitlement_female_stats["q1"]),
                entitlement_amount_female_q2=dict(entitlement_female_stats["q2"]),
                entitlement_amount_female_q3=dict(entitlement_female_stats["q3"]),
            )
        )

    def compute_stats_dict(self, entitlements_dict: dict[int, list[float]]) -> dict:
        # Returns a dict of stats per benefit_code_id for each stat
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
                stats["q1"][benefit_code_id] = round(
                    float(np.percentile(arr, 25, method="midpoint")), 2
                )
                stats["q2"][benefit_code_id] = round(
                    float(np.percentile(arr, 50, method="midpoint")), 2
                )
                stats["q3"][benefit_code_id] = round(
                    float(np.percentile(arr, 75, method="midpoint")), 2
                )
                stats["total"][benefit_code_id] = float(np.sum(arr))
        return stats
