from openg2p_pbms_models.models import G2PRegistry
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import mapped_column


class G2PFarmerRegistry(G2PRegistry):
    __tablename__ = "g2p_farmer_registry"

    name = mapped_column(String, nullable=False)
    gender = mapped_column(String, nullable=True)  # 'male' or 'female'
    land_area = mapped_column(Float, nullable=True)
    no_of_cattle_heads = mapped_column(Integer, nullable=True)
    no_of_poultry_heads = mapped_column(Integer, nullable=True)
    annual_income = mapped_column(Float, nullable=True)
    large_area_id = mapped_column(Integer, nullable=True)
    large_area_code = mapped_column(String, nullable=True)
    small_area_id = mapped_column(Integer, nullable=True)
    small_area_code = mapped_column(String, nullable=True)
