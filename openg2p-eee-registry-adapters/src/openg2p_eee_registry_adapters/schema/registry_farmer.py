from typing import Optional

from .registry import G2PRegistryPayload


class G2PFarmerRegistryPayload(G2PRegistryPayload):
    name: str
    land_area: Optional[float] = None
    no_of_cattle_heads: Optional[int] = None
    no_of_poultry_heads: Optional[int] = None
