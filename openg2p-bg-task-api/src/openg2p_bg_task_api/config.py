from openg2p_g2pconnect_common_lib.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="bg_task_api_", env_file=".env", extra="allow"
    )

    openapi_title: str = "OpenG2P PBMS Background Task API"
    openapi_description: str = """
        FastAPI Service for OpenG2P PBMS Background Task
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    db_datasource_bg_task: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/bgtaskdb"
    )
    db_datasource_sr: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/socialregistrydb"
    )
