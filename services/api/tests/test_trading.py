import pytest


@pytest.mark.django_db
class TestAllocate:

    def test_allocate_success(self, authenticated_client):
        """User can allocate funds successfully."""
        response = authenticated_client.post("/api/trading/allocate", {
            "amount": 500.00,
        }, format="json")

        assert response.status_code == 200
        assert response.data["data"]["allocated_usd"] == "500.00"

    def test_allocate_multiple_times(self, authenticated_client):
        """Allocating multiple times accumulates the balance."""
        authenticated_client.post("/api/trading/allocate", {"amount": 500.00}, format="json")
        response = authenticated_client.post("/api/trading/allocate", {"amount": 300.00}, format="json")

        assert response.status_code == 200
        assert response.data["data"]["allocated_usd"] == "800.00"

    def test_allocate_zero_amount(self, authenticated_client):
        """Allocating zero or negative amount fails."""
        response = authenticated_client.post("/api/trading/allocate", {
            "amount": 0,
        }, format="json")

        assert response.status_code == 400

    def test_allocate_requires_auth(self, api_client):
        """Unauthenticated request is rejected."""
        response = api_client.post("/api/trading/allocate", {
            "amount": 500.00,
        }, format="json")

        assert response.status_code == 401


@pytest.mark.django_db
class TestWithdraw:

    def test_withdraw_success(self, authenticated_client):
        """User can withdraw from allocated balance."""
        authenticated_client.post("/api/trading/allocate", {"amount": 500.00}, format="json")
        response = authenticated_client.post("/api/trading/withdraw", {
            "amount_usd": 200.00,
        }, format="json")

        assert response.status_code == 200
        assert response.data["data"]["allocated_usd"] == "300.00"

    def test_withdraw_insufficient_balance(self, authenticated_client):
        """Withdrawing more than allocated fails."""
        authenticated_client.post("/api/trading/allocate", {"amount": 100.00}, format="json")
        response = authenticated_client.post("/api/trading/withdraw", {
            "amount_usd": 500.00,
        }, format="json")

        assert response.status_code == 400
        assert response.data["error"] == "Insufficient allocated balance"

    def test_withdraw_zero_amount(self, authenticated_client):
        """Withdrawing zero fails."""
        response = authenticated_client.post("/api/trading/withdraw", {
            "amount_usd": 0,
        }, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestToggle:

    def test_toggle_start_success(self, authenticated_client):
        """User can start trading after allocating funds."""
        authenticated_client.post("/api/trading/allocate", {"amount": 500.00}, format="json")
        response = authenticated_client.post("/api/trading/toggle", {
            "desired_state": "START",
        }, format="json")

        assert response.status_code == 200
        assert response.data["data"]["trading_state"] == "RUNNING"

    def test_toggle_stop_success(self, authenticated_client):
        """User can stop trading."""
        authenticated_client.post("/api/trading/allocate", {"amount": 500.00}, format="json")
        authenticated_client.post("/api/trading/toggle", {"desired_state": "START"}, format="json")
        response = authenticated_client.post("/api/trading/toggle", {
            "desired_state": "STOP",
        }, format="json")

        assert response.status_code == 200
        assert response.data["data"]["trading_state"] == "STOPPED"

    def test_toggle_start_without_balance(self, authenticated_client):
        """Cannot start trading with zero balance."""
        response = authenticated_client.post("/api/trading/toggle", {
            "desired_state": "START",
        }, format="json")

        assert response.status_code == 400
        assert "zero" in response.data["error"].lower()

    def test_toggle_invalid_state(self, authenticated_client):
        """Invalid desired_state is rejected."""
        response = authenticated_client.post("/api/trading/toggle", {
            "desired_state": "INVALID",
        }, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestStatus:

    def test_status_returns_account(self, authenticated_client):
        """Status endpoint returns trading account data."""
        response = authenticated_client.get("/api/trading/status")

        assert response.status_code == 200
        assert "trading_state" in response.data["data"]
        assert "allocated_usd" in response.data["data"]

    def test_status_requires_auth(self, api_client):
        """Unauthenticated request is rejected."""
        response = api_client.get("/api/trading/status")

        assert response.status_code == 401