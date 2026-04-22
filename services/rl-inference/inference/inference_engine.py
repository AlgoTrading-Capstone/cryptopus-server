"""
Inference engine — runs the RL policy on state vectors and publishes actions to Redis.

Flow per tick:
1. Read state vector from Redis (written by trading-engine)
2. Run policy forward pass
3. Clip action to [-1, 1]
4. Write action back to Redis (read by trading-engine)
"""

import logging
import numpy as np
import torch
from shared.redis_client import RedisClient
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

def create_redis_client() -> RedisClient:
    return RedisClient(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
    )

logger = logging.getLogger(__name__)


class InferenceEngine:
    """
    Runs PyTorch policy forward pass for all active users.
    Reads state from Redis, writes action back to Redis.
    """

    def __init__(self, policy: torch.nn.Module, metadata: dict, redis_client: RedisClient):
        self._policy = policy
        self._metadata = metadata
        self._redis = redis_client

        # Extract critical dimensions from metadata
        self._state_dim = metadata["env_spec"]["state_dim"]
        self._action_dim = metadata["env_spec"]["action_dim"]

        logger.info(
            f"InferenceEngine ready: state_dim={self._state_dim}, "
            f"action_dim={self._action_dim}"
        )

    def run_for_all_users(self) -> int:
        """
        Run inference for all active users.
        Returns number of users processed.
        """
        active_users = self._redis.get_active_users()
        if not active_users:
            logger.debug("No active users — skipping inference")
            return 0

        processed = 0
        for user_id in active_users:
            try:
                self._run_for_user(user_id)
                processed += 1
            except Exception as e:
                logger.error(f"Inference failed for user {user_id}: {e}")

        logger.info(f"Inference completed for {processed}/{len(active_users)} users")
        return processed

    def _run_for_user(self, user_id: str) -> None:
        """
        Run one inference cycle for a single user.

        Reads: inference:state:{user_id}
        Writes: inference:action:{user_id}
        """
        # Read state from Redis
        state_data = self._redis.get(f"inference:state:{user_id}")
        if not state_data:
            logger.debug(f"No state available for user {user_id}")
            return

        state_list = state_data.get("state")
        if not state_list:
            return

        # Validate state dimension
        if len(state_list) != self._state_dim:
            logger.error(
                f"State dim mismatch for user {user_id}: "
                f"expected {self._state_dim}, got {len(state_list)}"
            )
            return

        # Build input tensor
        state = np.array(state_list, dtype=np.float32)
        state_tensor = torch.as_tensor(state, dtype=torch.float32).unsqueeze(0)

        # Forward pass — no gradient needed
        with torch.no_grad():
            action_tensor = self._policy(state_tensor)

        # Clip to [-1, 1] — both a_pos and a_sl
        action = action_tensor.squeeze(0).numpy()
        action = np.clip(action, -1.0, 1.0).tolist()

        # Write action to Redis for trading-engine
        self._redis.set(
            f"inference:action:{user_id}",
            {
                "action": action,
                "state_dim": self._state_dim,
                "timestamp": state_data.get("timestamp"),
            },
            ttl=120,  # expire after 2 minutes — stale actions should not be used
        )

        logger.debug(f"Action for user {user_id}: a_pos={action[0]:.3f}, a_sl={action[1]:.3f}")