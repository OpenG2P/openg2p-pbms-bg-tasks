from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="eee_celery_beat_", env_file=".env", extra="allow"
    )
    openapi_title: str = "OpenG2P EEE Celery Tasks"
    openapi_description: str = """
        Celery tasks for OpenG2P Eligibility Entitlement Engine
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    db_datasource_eee: str = "postgresql://postgres:postgres@localhost:5432/eeedb"
    db_datasource_sr: str = (
        "postgresql://postgres:postgres@localhost:5432/socialregistrydb"
    )
    db_datasource_pbms: str = "postgresql://postgres:postgres@localhost:5432/pbmsdb"

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"

    eee_task_worker_queue: str = "eee_task_worker_queue"

    producer_frequency: int = 10
    batch_size: int = 10000
