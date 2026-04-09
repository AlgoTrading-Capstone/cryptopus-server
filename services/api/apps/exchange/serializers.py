from rest_framework import serializers
from apps.exchange.models import ExchangeConnection


class ConnectExchangeSerializer(serializers.Serializer):
    api_key = serializers.CharField()
    api_secret = serializers.CharField(write_only=True)


class ValidateExchangeSerializer(serializers.Serializer):
    connection_id = serializers.CharField()


class DisconnectExchangeSerializer(serializers.Serializer):
    connection_id = serializers.CharField()


class ExchangeConnectionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeConnection
        fields = [
            "id",
            "exchange",
            "connected",
            "validated",
            "last_checked_at",
            "created_at",
        ]