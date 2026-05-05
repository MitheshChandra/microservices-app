from flask import Flask, jsonify, request
import uuid
import random
import time

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "payment-service"
    }), 200

@app.route('/payments', methods=['POST'])
def process_payment():
    try:
        data = request.json

        required_fields = ['order_id', 'amount', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        order_id = data['order_id']
        amount = data['amount']
        payment_method = data['payment_method']

        # Simulate payment processing delay
        time.sleep(1)

        # Simulate success/failure
        payment_success = random.choice([True, True, True, False])

        transaction_id = str(uuid.uuid4())

        if payment_success:
            return jsonify({
                "transaction_id": transaction_id,
                "order_id": order_id,
                "amount": amount,
                "payment_method": payment_method,
                "status": "success",
                "message": "Payment processed successfully"
            }), 200

        return jsonify({
            "transaction_id": transaction_id,
            "order_id": order_id,
            "amount": amount,
            "payment_method": payment_method,
            "status": "failed",
            "message": "Payment failed"
        }), 402

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/payments/<transaction_id>', methods=['GET'])
def get_payment_status(transaction_id):
    return jsonify({
        "transaction_id": transaction_id,
        "status": "success",
        "message": "Payment status fetched successfully"
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)