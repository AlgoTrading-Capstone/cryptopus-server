"""
Cryptopus Trading Engine — Entry Point

Starts the APScheduler-based tick engine that:
1. Reads active users from Redis
2. Fetches OHLCV from Kraken
3. Runs trading strategies
4. Builds RL state vector
5. Executes orders based on RL actions
"""

import logging
import signal
import sys
import time

from engine.tick_engine import TickEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Cryptopus Trading Engine")

    engine = TickEngine()

    def handle_shutdown(signum, frame):
        logger.info("Shutdown signal received — stopping engine")
        engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    engine.start()

    logger.info("Trading engine running — press Ctrl+C to stop")

    # Keep main thread alive
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()