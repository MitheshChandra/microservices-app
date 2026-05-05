import importlib.util
from pathlib import Path


def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT_DIR = Path(__file__).resolve().parents[1]
PAYMENT_SERVICE_PATH = ROOT_DIR / "payment-service" / "app.py"

payment_service = load_module("payment_service_app", PAYMENT_SERVICE_PATH)


def test_payment_service_health():
    client = payment_service.app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"
    assert response.get_json()["service"] == "payment-service"


def test_payment_service_missing_required_field():
    client = payment_service.app.test_client()

    response = client.post(
        "/payments",
        json={
            "order_id": 101,
            "amount": 999.99
        }
    )

    assert response.status_code == 400
    assert "payment_method is required" in response.get_json()["error"]


def test_payment_service_successful_payment(monkeypatch):
    monkeypatch.setattr(payment_service.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(payment_service.random, "choice", lambda values: True)

    client = payment_service.app.test_client()

    response = client.post(
        "/payments",
        json={
            "order_id": 101,
            "amount": 999.99,
            "payment_method": "card"
        }
    )

    response_body = response.get_json()

    assert response.status_code == 200
    assert response_body["status"] == "success"
    assert response_body["order_id"] == 101
    assert response_body["amount"] == 999.99
    assert response_body["payment_method"] == "card"
    assert "transaction_id" in response_body


def test_get_payment_status():
    client = payment_service.app.test_client()

    response = client.get("/payments/test-transaction-id")

    assert response.status_code == 200
    assert response.get_json()["transaction_id"] == "test-transaction-id"