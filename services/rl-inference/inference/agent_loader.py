"""
Agent loader — loads model artifacts from S3 or local path.

Local mode: set LOCAL_MODEL_PATH and LOCAL_METADATA_PATH env vars.
S3 mode: set S3_BUCKET, AWS credentials, and use s3:// paths.
"""

import json
import logging
import sys
import torch
import boto3
from config import ELEGANTRL_PATH, LOCAL_MODEL_PATH, LOCAL_METADATA_PATH
from config import S3_BUCKET, S3_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
logger = logging.getLogger(__name__)


class AgentLoader:
    """
    Loads RL model artifacts from S3 or local filesystem.
    Local mode is used for development and debugging.
    """

    def load(self, s3_model_path: str, s3_metadata_path: str) -> tuple:
        """
        Load act.pth and metadata.json.
        Uses local paths if LOCAL_MODEL_PATH is set, otherwise downloads from S3.

        Returns:
            (policy, metadata) tuple
        """
        if LOCAL_MODEL_PATH and LOCAL_METADATA_PATH:
            logger.info("Local model mode — skipping S3 download")
            model_local = LOCAL_MODEL_PATH
            metadata_local = LOCAL_METADATA_PATH
        else:
            logger.info("S3 mode — downloading model artifacts")
            model_local, metadata_local = self._download_from_s3(
                s3_model_path, s3_metadata_path
            )

        metadata = self._load_metadata(metadata_local)
        policy = self._load_policy(model_local)

        return policy, metadata

    def _download_from_s3(self, s3_model_path: str, s3_metadata_path: str) -> tuple:
        """Download artifacts from S3 to /tmp."""
        s3 = boto3.client(
            "s3",
            region_name=S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        model_local = "/tmp/act.pth"
        metadata_local = "/tmp/metadata.json"

        self._download_file(s3, s3_model_path, model_local)
        self._download_file(s3, s3_metadata_path, metadata_local)

        return model_local, metadata_local

    def _download_file(self, s3_client, s3_uri: str, local_path: str) -> None:
        """Download a single file from S3 URI."""
        bucket, key = self._parse_s3_uri(s3_uri)
        try:
            s3_client.download_file(bucket, key, local_path)
            logger.info(f"Downloaded s3://{bucket}/{key} → {local_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to download {s3_uri}: {e}")

    def _load_metadata(self, local_path: str) -> dict:
        """Load and validate metadata.json."""
        with open(local_path, "r") as f:
            metadata = json.load(f)

        required = ["env_spec", "strategies", "data"]
        for field in required:
            if field not in metadata:
                raise ValueError(f"metadata.json missing required field: {field}")

        state_dim = metadata["env_spec"]["state_dim"]
        strategy_list = metadata["strategies"]["strategy_list"]
        logger.info(f"Metadata loaded: state_dim={state_dim}, strategies={len(strategy_list)}")

        return metadata

    def _load_policy(self, local_path: str) -> torch.nn.Module:
        """
        Load act.pth — pickled nn.Module.
        Requires ElegantRL on sys.path before unpickling.
        """
        if ELEGANTRL_PATH not in sys.path:
            sys.path.insert(0, ELEGANTRL_PATH)
            logger.info(f"Added ElegantRL to sys.path: {ELEGANTRL_PATH}")

        try:
            policy = torch.load(
                local_path,
                map_location=torch.device("cpu"),
                weights_only=False,
            )
            policy.eval()
            logger.info(f"Policy loaded from {local_path}")
            return policy
        except Exception as e:
            raise RuntimeError(f"Failed to load policy: {e}")

    @staticmethod
    def _parse_s3_uri(s3_uri: str) -> tuple:
        """Parse s3://bucket/key into (bucket, key)."""
        if not s3_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        parts = s3_uri[5:].split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI: {s3_uri}")
        return parts[0], parts[1]