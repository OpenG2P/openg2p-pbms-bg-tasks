from sqlalchemy.ext.asyncio import create_async_engine

from .config import Settings

_config = Settings.get_config()


def get_engine():
    if _config.db_datasource:
        db_engine_bg_task = create_async_engine(_config.db_datasource_bg_task)
        db_engine_sr = create_async_engine(_config.db_datasource_sr)
        return {
            "db_engine_bg_task": db_engine_bg_task,
            "db_engine_sr": db_engine_sr,
        }
