import os

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
import logging


def init_sentry():
    sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.INFO)
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[sentry_logging],
        traces_sample_rate=1.0
    )
    logging.getLogger(__name__).info("Sentry initialized.")
