from rest_framework import serializers
from apps.trading.models import TradingAccount


class AllocateSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=0.01)


class WithdrawSerializer(serializers.Serializer):
    amount_usd = serializers.FloatField(min_value=0.01)


class ToggleSerializer(serializers.Serializer):
    desired_state = serializers.ChoiceField(choices=["START", "STOP"])


class TradingAccountResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingAccount
        fields = [
            "id",
            "trading_state",
            "allocated_usd",
            "state_changed_at",
            "created_at",
            "updated_at",
        ]