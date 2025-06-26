# ruff: noqa: E402

from .config import Settings

_config = Settings.get_config()

from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_fastapi_common.exception import BaseExceptionHandler
from sqlalchemy import create_engine


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
        return {
            "db_engine_eee": db_engine_eee,
            "db_engine_sr": db_engine_sr,
            "db_engine_pbms": db_engine_pbms,
        }


celery_app = Celery(
    "g2p_eee_celery_beat_producer",
    broker=_config.celery_broker_url,
    backend=_config.celery_backend_url,
    include=["openg2p_eee_celery_beat_producers.tasks"],
)

celery_app.conf.beat_schedule = {
    "beneficiary_list_beat_producer": {
        "task": "beneficiary_list_beat_producer",
        "schedule": _config.producer_frequency,
    },
    "entitlement_beat_producer": {
        "task": "entitlement_beat_producer",
        "schedule": _config.producer_frequency,
    },
    "disbursement_envelope_creation_beat_producer": {
        "task": "disbursement_envelope_creation_beat_producer",
        "schedule": _config.producer_frequency,
    },
    "disbursement_batch_creation_beat_producer": {
        "task": "disbursement_batch_creation_beat_producer",
        "schedule": _config.producer_frequency,
    },
    "disbursement_beat_producer": {
        "task": "disbursement_beat_producer",
        "schedule": _config.producer_frequency,
    },
}
celery_app.conf.timezone = "UTC"
