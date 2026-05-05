from flask import Flask, jsonify, request
import psycopg2
import os
import time

app = Flask(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'database': os.getenv('DB_NAME', 'appdb'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123')
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    retries = 5

    while retries > 0:
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    product_name VARCHAR(200) NOT NULL,
                    quantity INTEGER NOT NULL,
                    total_price DECIMAL(10, 2) NOT NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            cur.close()
            conn.close()

            print("Order service database initialized successfully")
            return

        except Exception as e:
            print(f"Database not ready yet. Retrying... Error: {e}")
            retries -= 1
            time.sleep(5)

    print("Failed to initialize order service database after retries")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "order-service"
    }), 200

@app.route('/orders', methods=['GET'])
def get_orders():
    try:
        init_db()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('''
            SELECT id, user_id, product_name, quantity, total_price, status, created_at
            FROM orders
            ORDER BY id DESC
        ''')

        orders = cur.fetchall()

        cur.close()
        conn.close()

        orders_list = [
            {
                "id": order[0],
                "user_id": order[1],
                "product_name": order[2],
                "quantity": order[3],
                "total_price": float(order[4]),
                "status": order[5],
                "created_at": str(order[6])
            }
            for order in orders
        ]

        return jsonify(orders_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/orders', methods=['POST'])
def create_order():
    try:
        init_db()

        data = request.json

        required_fields = ['user_id', 'product_name', 'quantity', 'total_price']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            '''
            INSERT INTO orders (user_id, product_name, quantity, total_price)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            ''',
            (
                data['user_id'],
                data['product_name'],
                data['quantity'],
                data['total_price']
            )
        )

        order_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "id": order_id,
            "message": "Order created successfully",
            "status": "pending"
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/orders/<int:order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    try:
        data = request.json

        if 'status' not in data:
            return jsonify({"error": "status is required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            '''
            UPDATE orders
            SET status = %s
            WHERE id = %s
            RETURNING id
            ''',
            (data['status'], order_id)
        )

        updated_order = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        if not updated_order:
            return jsonify({"error": "Order not found"}), 404

        return jsonify({
            "id": order_id,
            "message": "Order status updated successfully",
            "status": data['status']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)