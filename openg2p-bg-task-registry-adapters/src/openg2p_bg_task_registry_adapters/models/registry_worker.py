from openg2p_pbms_models.models import G2PRegistry
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column


class G2PWorkerRegistry(G2PRegistry):
    __tablename__ = "g2p_worker_registry"

    name = mapped_column(String, nullable=False)
    email = mapped_column(String, nullable=False)
    phone = mapped_column(String, nullable=False)

    age_group = mapped_column(String, nullable=True)  # "18_35", "36_54", "55_plus"
    province_id = mapped_column(Integer, nullable=True)
    district_id = mapped_column(Integer, nullable=True)
    constituency_id = mapped_column(Integer, nullable=True)
    ward_id = mapped_column(Integer, nullable=True)
