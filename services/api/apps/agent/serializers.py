from rest_framework import serializers
from apps.agent.models import Agent


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = [
            "id",
            "name",
            "version",
            "status",
            "activated_at",
            "created_at",
        ]


class AgentMetricsQuerySerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=["7d", "30d", "90d", "1y"], default="30d")


class AgentPlotsQuerySerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=["7d", "30d", "90d", "1y"], default="30d")