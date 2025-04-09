from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="eee_celery_workers_", env_file=".env", extra="allow"
    )
    openapi_title: str = "OpenG2P EEE Celery Workers"
    openapi_description: str = """
        Celery workers for OpenG2P Eligibility Entitlement Engine
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

    g2p_bridge_disbursement_url: str = (
        "https://g2p-bridge.dev.openg2p.org/api/g2p-bridge/create_disbursements"
    )
    g2p_bridge_envelope_creation_url: str = (
        "https://g2p-bridge.dev.openg2p.org/api/g2p-bridge/create_disbursement_envelope"
    )
    disbursement_batch_size: int = 500

    batch_size: int = 10000

    # Authentication parameters
    # auth_url: str = "https://idgenerator.loadtest.openg2p.org/v1/idgenerator/token"
    # auth_client_id: str = "idgenerator"
    # auth_client_secret: str = "idgenerator"
    # auth_grant_type: str = "client_credentials"

    # worker_type_max_attempts: dict[str, int] = {
    #     "max_id_generation_request_attempts": 4,
    #     "max_id_generation_update_attempts": 4,
    # }
