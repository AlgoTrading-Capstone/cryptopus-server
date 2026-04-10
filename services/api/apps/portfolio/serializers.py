from rest_framework import serializers
from apps.portfolio.models import Trade


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = [
            "id",
            "symbol",
            "side",
            "quantity",
            "price",
            "fee",
            "realized_pnl",
            "executed_at",
            "kraken_order_id",
        ]


class TradesQuerySerializer(serializers.Serializer):
    # Page number to retrieve (starts at 1)
    page = serializers.IntegerField(min_value=1, default=1)
    # Number of trades per page (max 100 to prevent overloading the response)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)
    # Optional filter by trading pair (e.g. "BTC/USD")
    symbol = serializers.CharField(required=False)
    # Optional filter — return only trades after this datetime
    from_date = serializers.DateTimeField(required=False)
    # Optional filter — return only trades before this datetime
    to_date = serializers.DateTimeField(required=False)


class PerformanceQuerySerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=["7d", "30d", "90d", "1y"], default="30d")


class EquityHistoryQuerySerializer(serializers.Serializer):
    range = serializers.ChoiceField(choices=["7d", "30d", "90d", "1y"], default="7d")
    interval = serializers.ChoiceField(choices=["1h", "4h", "1d"], default="1h")