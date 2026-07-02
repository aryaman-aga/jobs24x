from django.apps import AppConfig
import os
import threading
import logging

logger = logging.getLogger(__name__)


def _start_keep_alive():
    import time
    import urllib.request

    url = os.environ.get('KEEP_ALIVE_URL', '').rstrip('/')
    if not url:
        logger.info("Keep-alive: no KEEP_ALIVE_URL set, skipping")
        return

    logger.info(f"Keep-alive thread started, pinging {url}/health/ every 10 min")
    while True:
        try:
            urllib.request.urlopen(f"{url}/health/", timeout=10)
            logger.debug("Keep-alive ping OK")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        time.sleep(600)


class CoreConfig(AppConfig):
    name = 'apps.core'
    label = 'core'

    def ready(self):
        url = os.environ.get('KEEP_ALIVE_URL', '')
        in_dev_reloader = os.environ.get('RUN_MAIN') == 'true'

        if url:
            if in_dev_reloader:
                pass
            elif os.environ.get('IGNORE_KEEP_ALIVE'):
                pass
            else:
                thread = threading.Thread(target=_start_keep_alive, daemon=True)
                thread.start()
