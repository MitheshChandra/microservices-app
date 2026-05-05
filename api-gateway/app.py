from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user-service:5001')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://order-service:5002')
PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL', 'http://payment-service:5003')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "api-gateway"}), 200

@app.route('/api/users', methods=['GET', 'POST'])
def users():
    try:
        if request.method == 'GET':
            response = requests.get(f'{USER_SERVICE_URL}/users')
        else:
            response = requests.post(f'{USER_SERVICE_URL}/users', json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders', methods=['GET', 'POST'])
def orders():
    try:
        if request.method == 'GET':
            response = requests.get(f'{ORDER_SERVICE_URL}/orders')
        else:
            response = requests.post(f'{ORDER_SERVICE_URL}/orders', json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/payments', methods=['POST'])
def payments():
    try:
        response = requests.post(f'{PAYMENT_SERVICE_URL}/payments', json=request.json)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)