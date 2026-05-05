# Microservices Application

Python Flask-based microservices for e-commerce platform.

## Services

- **api-gateway** (port 5000) - API Gateway routing requests
- **user-service** (port 5001) - User management with PostgreSQL
- **order-service** (port 5002) - Order management with PostgreSQL
- **payment-service** (port 5003) - Payment processing

## Local Development

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Code quality check
flake8 .