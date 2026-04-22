"""
Cryptopus RL Inference Service — Entry Point

Loads the trained RL policy from S3 (or local path for development)
and runs inference for all active users on a fixed interval.

Flow:
1. Load active agent metadata from Redis
2. Download act.pth + metadata.json from S3 (or local)
3. Start inference loop — every INFERENCE_INTERVAL_SECONDS:
   a. Read state vectors from Redis (written by trading-engine)
   b. Run policy forward pass
   c. Write actions back to Redis (read by trading-engine)
"""

import logging
import signal
import sys
import time

from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB, INFERENCE_INTERVAL_SECONDS
from shared.redis_client import RedisClient
from inference.agent_loader import AgentLoader
from inference.inference_engine import InferenceEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Cryptopus RL Inference Service")

    # Connect to Redis
    redis_client = RedisClient(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
    )

    if not redis_client.ping():
        logger.error("Cannot connect to Redis — exiting")
        sys.exit(1)

    logger.info("Redis connected")

    # Load active agent from Redis
    agent_meta = redis_client.get_active_agent()
    if not agent_meta:
        logger.error("No active agent found in Redis — exiting")
        sys.exit(1)

    s3_model_path = agent_meta.get("s3_model_path")
    s3_metadata_path = agent_meta.get("s3_metadata_path")

    if not s3_model_path or not s3_metadata_path:
        logger.error("Active agent missing s3_model_path or s3_metadata_path — exiting")
        sys.exit(1)

    # Load policy and metadata
    loader = AgentLoader()
    policy, metadata = loader.load(s3_model_path, s3_metadata_path)

    # Initialize inference engine
    engine = InferenceEngine(
        policy=policy,
        metadata=metadata,
        redis_client=redis_client,
    )

    # Graceful shutdown
    def handle_shutdown(signum, frame):
        logger.info("Shutdown signal received — stopping inference service")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    logger.info(f"Inference loop starting — interval={INFERENCE_INTERVAL_SECONDS}s")

    # Inference loop
    while True:
        try:
            processed = engine.run_for_all_users()
            logger.info(f"Inference cycle complete — processed {processed} users")
        except Exception as e:
            logger.error(f"Inference cycle failed: {e}")

        time.sleep(INFERENCE_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()