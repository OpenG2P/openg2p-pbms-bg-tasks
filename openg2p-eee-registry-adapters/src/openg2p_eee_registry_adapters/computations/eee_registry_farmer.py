from typing import List

import numpy as np
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ..interface import EEERegistryInterface
from ..models import EligibilitySummaryFarmer, G2PFarmerRegistry
from ..schema import EligibilitySummaryFarmerResponse


class EEERegistryFarmer(EEERegistryInterface):
    """Fetches farmer data and computes summary statistics"""

    async def get_summary(
        self, request_id: int, eee_session: Session
    ) -> EligibilitySummaryFarmerResponse:
        eligibility_summary_farmer = (
            (
                await eee_session.execute(
                    select(EligibilitySummaryFarmer).where(
                        EligibilitySummaryFarmer.eligibility_request_id == request_id
                    )
                )
            )
            .scalars()
            .first()
        )

        summary = EligibilitySummaryFarmerResponse(
            id=eligibility_summary_farmer.id,
            program_id=eligibility_summary_farmer.program_id,
            program_mnemonic=eligibility_summary_farmer.program_mnemonic,
            target_registry_type=eligibility_summary_farmer.target_registry_type,
            eligibility_request_id=eligibility_summary_farmer.eligibility_request_id,
            number_of_registrants=eligibility_summary_farmer.number_of_registrants,
            date_created=eligibility_summary_farmer.date_created,
            land_holding_mean=eligibility_summary_farmer.land_holding_mean,
            land_holding_quartile_25=eligibility_summary_farmer.land_holding_quartile_25,
            land_holding_quartile_50=eligibility_summary_farmer.land_holding_quartile_50,
            land_holding_quartile_75=eligibility_summary_farmer.land_holding_quartile_75,
            annual_income_mean=eligibility_summary_farmer.annual_income_mean,
            annual_income_quartile_25=eligibility_summary_farmer.annual_income_quartile_25,
            annual_income_quartile_50=eligibility_summary_farmer.annual_income_quartile_50,
            annual_income_quartile_75=eligibility_summary_farmer.annual_income_quartile_75,
        )

        return summary

    def get_registrants(self, registrant_ids, sr_session) -> List[G2PFarmerRegistry]:
        return (
            sr_session.query(G2PFarmerRegistry)
            .filter(G2PFarmerRegistry.id.in_(registrant_ids))
            .all()
        )

    def compute_and_persist_summary(
        self, registrant_ids, base_summary, sr_session: Session, eee_session: Session
    ):
        registrants = self.get_registrants(registrant_ids, sr_session)
        land_areas = [
            farmer.land_area for farmer in registrants if farmer.land_area is not None
        ]

        farmer_summary = EligibilitySummaryFarmer(
            program_id=base_summary.program_id,
            program_mnemonic=base_summary.program_mnemonic,
            target_registry_type=base_summary.target_registry_type,
            eligibility_request_id=base_summary.eligibility_request_id,
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
