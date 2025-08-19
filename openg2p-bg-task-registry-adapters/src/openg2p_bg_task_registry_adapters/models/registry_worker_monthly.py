from openg2p_pbms_models.models import G2PRegistry
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column

class G2PWorkerMonthlyRegistry(G2PRegistry):
    __tablename__ = "g2p_worker_monthly_registry"

    unique_id = mapped_column(Integer, nullable=True)
    name = mapped_column(String, nullable=False)
    attendance_month = mapped_column(String, nullable=False)
    source_type = mapped_column(String, nullable=True)
