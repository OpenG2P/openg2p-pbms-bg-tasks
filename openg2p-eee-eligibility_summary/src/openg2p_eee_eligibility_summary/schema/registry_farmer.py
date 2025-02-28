from typing import Optional

from .registry import G2PRegistry


class G2PFarmerRegistry(G2PRegistry):
    name: str
    land_area: Optional[float]
    no_of_cattle_heads: Optional[int]
    no_of_poultry_heads: Optional[int]
