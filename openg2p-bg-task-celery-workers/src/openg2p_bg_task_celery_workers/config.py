from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="bg_task_celery_workers_", env_file=".env", extra="allow"
    )
    openapi_title: str = "OpenG2P PBMS Background Task Celery Workers"
    openapi_description: str = """
        Celery workers for OpenG2P PBMS Background Task
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    db_datasource_bg_task: str = (
        "postgresql://postgres:postgres@localhost:5432/bgtaskdb"
    )
    db_datasource_sr: str = (
        "postgresql://postgres:postgres@localhost:5432/socialregistrydb"
    )
    db_datasource_pbms: str = "postgresql://postgres:postgres@localhost:5432/pbmsdb"
    db_datasource_bg_task_async: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bgtaskdb"
    )

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_backend_url: str = "redis://localhost:6379/0"

    # TODO: separate base_url, endpoints
    g2p_bridge_disbursement_url: str = "http://g2p_bridge_disbursement_url"
    g2p_bridge_envelope_creation_url: str = "http://g2p_bridge_envelope_creation_url"

    batch_size: int = 2000
    worker_max_attempts: int = 5

    sign_key_keymanager_app_id: str = "PBMS"
    sign_key_keymanager_ref_id: str = ""

    keymanager_api_timeout: int = 10
    keymanager_api_base_url: str = ""
    keymanager_auth_enabled: bool = True
    keymanager_auth_url: str = ""
    keymanager_auth_client_id: str = "openg2p-pbms"
    keymanager_auth_client_secret: str = ""
