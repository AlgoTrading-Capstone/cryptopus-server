import json
import logging
import redis

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis wrapper for the trading engine.
    Handles connection, serialization, and key conventions.
    """

    def __init__(self, host: str, port: int, password: str = None, db: int = 0):
        self._client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True,
        )

    def ping(self) -> bool:
        """Check if Redis is reachable."""
        try:
            return self._client.ping()
        except redis.RedisError as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    def get(self, key: str) -> dict | None:
        """Get a JSON value by key."""
        try:
            value = self._client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            return None

    def set(self, key: str, value: dict, ttl: int = None) -> bool:
        """Set a JSON value with optional TTL in seconds."""
        try:
            serialized = json.dumps(value)
            if ttl:
                self._client.setex(key, ttl, serialized)
            else:
                self._client.set(key, serialized)
            return True
        except (redis.RedisError, TypeError) as e:
            logger.error(f"Redis set failed for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a key."""
        try:
            self._client.delete(key)
            return True
        except redis.RedisError as e:
            logger.error(f"Redis delete failed for key {key}: {e}")
            return False

    def get_active_agent(self) -> dict | None:
        """Get the currently active agent metadata."""
        return self.get("agent:active")

    def get_trading_state(self, user_id: str) -> dict | None:
        """Get trading state for a specific user."""
        return self.get(f"trading:state:{user_id}")

    def get_position_state(self, user_id: str) -> dict | None:
        """Get open position state for a specific user."""
        return self.get(f"position:active:{user_id}")

    def set_position_state(self, user_id: str, position: dict) -> bool:
        """Save open position state for a specific user."""
        return self.set(f"position:active:{user_id}", position)

    def delete_position_state(self, user_id: str) -> bool:
        """Remove position state when position is closed."""
        return self.delete(f"position:active:{user_id}")

    def get_active_users(self) -> list[str]:
        """Get list of user IDs currently in RUNNING trading state."""
        try:
            keys = self._client.keys("trading:state:*")
            active_users = []
            for key in keys:
                state = self.get(key)
                if state and state.get("state") == "RUNNING":
                    user_id = key.replace("trading:state:", "")
                    active_users.append(user_id)
            return active_users
        except redis.RedisError as e:
            logger.error(f"Redis get_active_users failed: {e}")
            return []

    def publish_alert(self, user_id: str, event: dict) -> bool:
        """Publish an alert event to the user's Redis channel."""
        try:
            channel = f"events:alerts:{user_id}"
            self._client.publish(channel, json.dumps(event))
            return True
        except redis.RedisError as e:
            logger.error(f"Redis publish failed for user {user_id}: {e}")
            return False

    def set_engine_status(self, status: dict) -> bool:
        """Update the trading engine runtime status."""
        return self.set("agent:runtime:status", status)