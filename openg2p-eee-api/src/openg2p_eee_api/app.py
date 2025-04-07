# ruff: noqa: E402
import asyncio
import logging

from .config import Settings

_config = Settings.get_config()

from openg2p_eee_models.models import (
    Disbursement,
    DisbursementBatch,
    EEEDetails,
    EEESummary,
)
from openg2p_eee_registry_adapters.cache import init_cache
from openg2p_fastapi_common.app import Initializer as BaseInitializer

from .controllers import EEEBeneficiarySearchController, EEESummaryController
from .services import EEEBeneficiarySearchService, EEESummaryService

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()
        init_cache()
        EEESummaryService()
        EEEBeneficiarySearchService()
        EEESummaryController().post_init()
        EEEBeneficiarySearchController().post_init()

    def migrate_database(self, args):
        _logger.info(f"Database migration completed{_config.db_datasource_eee}")
        super().migrate_database(args)

        async def migrate():
            _logger.info("Migrating database")
            await DisbursementBatch.create_migrate()
            await Disbursement.create_migrate()
            await EEEDetails.create_migrate()
            await EEESummary.create_migrate()

        asyncio.run(migrate())
