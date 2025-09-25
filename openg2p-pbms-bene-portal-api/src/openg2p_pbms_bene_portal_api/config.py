from openg2p_g2pconnect_common_lib.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="pbms_bene_portal_api_", env_file=".env", extra="allow"
    )

    openapi_title: str = "OpenG2P PBMS Bene Portal API"
    openapi_description: str = """
        FastAPI Service for OpenG2P PBMS Bene Portal API
        ***********************************
        Further details goes here
        ***********************************
        """
    openapi_version: str = __version__

    db_dbname: str = "socialregistrydb"
