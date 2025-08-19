from typing import Optional

from .registry import G2PRegistryPayload


class G2PWorkerRegistryPayload(G2PRegistryPayload):
    unique_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    age_group: Optional[str] = None
    province_id: Optional[int] = None
    district_id: Optional[int] = None
    constituency_id: Optional[int] = None
    ward_id: Optional[int] = None
