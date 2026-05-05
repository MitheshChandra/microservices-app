import importlib.util
from pathlib import Path


def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT_DIR = Path(__file__).resolve().parents[1]
API_GATEWAY_PATH = ROOT_DIR / "api-gateway" / "app.py"

api_gateway = load_module("api_gateway_app", API_GATEWAY_PATH)


class MockResponse:
    def __init__(self, payload, status_code):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


def test_api_gateway_health():
    client = api_gateway.app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"
    assert response.get_json()["service"] == "api-gateway"


def test_api_gateway_get_users(monkeypatch):
    def fake_get(url):
        assert "user-service" in url
        return MockResponse(
            [
                {
                    "id": 1,
                    "name": "Test User",
                    "email": "test@example.com"
                }
            ],
            200
        )

    monkeypatch.setattr(api_gateway.requests, "get", fake_get)

    client = api_gateway.app.test_client()
    response = client.get("/api/users")

    assert response.status_code == 200
    assert response.get_json()[0]["name"] == "Test User"


def test_api_gateway_create_order(monkeypatch):
    def fake_post(url, json):
        assert "order-service" in url
        assert json["product_name"] == "Laptop"
        return MockResponse(
            {
                "id": 101,
                "message": "Order created successfully"
            },
            201
        )

    monkeypatch.setattr(api_gateway.requests, "post", fake_post)

    client = api_gateway.app.test_client()

    response = client.post(
        "/api/orders",
        json={
            "user_id": 1,
            "product_name": "Laptop",
            "quantity": 1,
            "total_price": 999.99
        }
    )

    assert response.status_code == 201
    assert response.get_json()["id"] == 101


def test_api_gateway_process_payment(monkeypatch):
    def fake_post(url, json):
        assert "payment-service" in url
        assert json["order_id"] == 101
        return MockResponse(
            {
                "transaction_id": "txn-123",
                "status": "success"
            },
            200
        )

    monkeypatch.setattr(api_gateway.requests, "post", fake_post)

    client = api_gateway.app.test_client()

    response = client.post(
        "/api/payments",
        json={
            "order_id": 101,
            "amount": 999.99,
            "payment_method": "card"
        }
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "success"