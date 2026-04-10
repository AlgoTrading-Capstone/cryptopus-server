from rest_framework import serializers
from apps.agent.models import Agent
from apps.authentication.models import User


class AgentUploadSerializer(serializers.Serializer):
    name = serializers.CharField()
    version = serializers.CharField()
    s3_model_path = serializers.CharField()
    s3_metadata_path = serializers.CharField()
    normalization_profile = serializers.CharField()
    strategy_set_hash = serializers.CharField()


class AgentActivateSerializer(serializers.Serializer):
    activation_mode = serializers.ChoiceField(choices=["STANDARD"], default="STANDARD")


class HotSwapSerializer(serializers.Serializer):
    from_agent_id = serializers.UUIDField()
    to_agent_id = serializers.UUIDField()


class AdminAgentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField()

    class Meta:
        model = Agent
        fields = [
            "id",
            "name",
            "version",
            "status",
            "normalization_profile",
            "strategy_set_hash",
            "uploaded_by",
            "activated_at",
            "created_at",
        ]


class UpdateUserStatusSerializer(serializers.Serializer):
    account_status = serializers.ChoiceField(
        choices=["ACTIVE", "SUSPENDED", "PENDING_VERIFICATION"]
    )


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "account_status",
            "role",
            "created_at",
        ]