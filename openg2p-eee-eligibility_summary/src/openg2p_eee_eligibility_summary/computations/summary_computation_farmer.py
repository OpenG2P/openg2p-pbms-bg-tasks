from typing import List

import numpy as np
from openg2p_eee_models.models import G2PEligibilitySummaryFarmer
from openg2p_sr_models.models import G2PFarmerRegistry
from sqlalchemy.orm import Session

from ..interface import SummaryComputationInterface


class SummaryComputationFarmer(SummaryComputationInterface):
    """Fetches farmer data and computes summary statistics"""

    def fetch_registrants(self, registrant_ids, sr_session) -> List[G2PFarmerRegistry]:
        return (
            sr_session.query(G2PFarmerRegistry)
            .filter(G2PFarmerRegistry.id.in_(registrant_ids))
            .all()
        )

    def compute_and_persist_summary(
        self, registrant_ids, base_summary, sr_session: Session, eee_session: Session
    ):
        registrants = self.fetch_registrants(registrant_ids, sr_session)
        land_areas = [
            farmer.land_area for farmer in registrants if farmer.land_area is not None
        ]

        farmer_summary = G2PEligibilitySummaryFarmer(
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
