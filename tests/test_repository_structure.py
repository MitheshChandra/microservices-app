from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

SERVICES = [
    "api-gateway",
    "user-service",
    "order-service",
    "payment-service"
]


def test_service_directories_exist():
    for service in SERVICES:
        service_dir = ROOT_DIR / service
        assert service_dir.exists(), f"{service} directory does not exist"


def test_each_service_has_dockerfile():
    for service in SERVICES:
        dockerfile = ROOT_DIR / service / "Dockerfile"
        assert dockerfile.exists(), f"{service} Dockerfile is missing"


def test_each_service_has_requirements_file():
    for service in SERVICES:
        requirements = ROOT_DIR / service / "requirements.txt"
        assert requirements.exists(), f"{service} requirements.txt is missing"


def test_each_service_has_app_file():
    for service in SERVICES:
        app_file = ROOT_DIR / service / "app.py"
        assert app_file.exists(), f"{service} app.py is missing"