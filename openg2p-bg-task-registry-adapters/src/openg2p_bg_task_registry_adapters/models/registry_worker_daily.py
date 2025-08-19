from openg2p_pbms_models.models import G2PRegistry
from sqlalchemy import Integer, String, Date, Text
from sqlalchemy.orm import mapped_column

class G2PWorkerDailyRegistry(G2PRegistry):
    __tablename__ = "g2p_worker_daily_registry"

    nrc_number = mapped_column(String, nullable=True)
    attendance_date = mapped_column(Date, nullable=True)
    task = mapped_column(Text, nullable=True)
