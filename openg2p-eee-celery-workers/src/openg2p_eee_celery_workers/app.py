# ruff: noqa: E402

from .config import Settings

_config = Settings.get_config()

from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.exception import BaseExceptionHandler
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().init_logger()
        super().init_app()
        BaseExceptionHandler()


def get_engine():
    if _config.db_datasource:
        db_engine_eee = create_engine(_config.db_datasource_eee)
        db_engine_sr = create_engine(_config.db_datasource_sr)
        db_engine_pbms = create_engine(_config.db_datasource_pbms)
        db_engine_eee_async = create_async_engine(_config.db_datasource_eee_async)
        return {
            "db_engine_eee": db_engine_eee,
            "db_engine_sr": db_engine_sr,
            "db_engine_pbms": db_engine_pbms,
            "db_engine_eee_async": db_engine_eee_async,
        }


celery_app = Celery(
    "g2p_eee_celery_worker",
    broker=_config.celery_broker_url,
    backend=_config.celery_backend_url,
    include=["openg2p_eee_celery_workers.tasks"],
)

celery_app.conf.timezone = "UTC"
