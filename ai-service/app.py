from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
import redis
from rq import Queue
import numpy as np
from sklearn.linear_model import LinearRegression
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import random

# Flask app setup
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# Redis setup
redis_conn = redis.Redis(host='localhost', port=6379)
task_queue = Queue(connection=redis_conn)

# PostgreSQL setup
DB_CONFIG = {
    'dbname': 'logistics_db',
    'user': 'postgres',
    'password': '4738',
    'host': 'localhost',
    'port': 5432
}

def get_db_conn():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# Model setup
MODEL_PATH = 'model.pkl'

def train_model():
    X = np.array([[1, 1], [2, 2], [3, 1.5], [4, 3]])
    y = np.array([10, 20, 22, 35])
    model = LinearRegression().fit(X, y)
    joblib.dump(model, MODEL_PATH)
    logging.info("Model trained and saved to disk.")

def load_model():
    if not os.path.exists(MODEL_PATH):
        logging.info("Model not found, training a new one...")
        train_model()
    return joblib.load(MODEL_PATH)

# Helper: insert random example data
def insert_sample_data(driver_id):
    conn = get_db_conn()
    cur = conn.cursor()

    # Random drug test
    test_result = random.choice(['pass', 'fail'])
    cur.execute("""
        INSERT INTO drug_tests (driver_id, result, test_date)
        VALUES (%s, %s, %s)
    """, (driver_id, test_result, datetime.now().date()))

    # Random violation
    if random.random() < 0.5:  # 50% chance
        violation_type = random.choice(['speeding', 'dui', 'reckless driving'])
        cur.execute("""
            INSERT INTO violations (driver_id, type, date)
            VALUES (%s, %s, %s)
        """, (driver_id, violation_type, datetime.now().date()))

    # Random credential check
    credential_type = random.choice(['license', 'medical', 'training'])
    valid = random.choice([True, False])
    cur.execute("""
        INSERT INTO credentials (driver_id, credential_type, valid, check_date)
        VALUES (%s, %s, %s, %s)
    """, (driver_id, credential_type, valid, datetime.now().date()))

    conn.commit()
    cur.close()
    conn.close()

# Prediction endpoint
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)
        X_input = [[data['distance_km'], data['fuel_used']]]
        driver_id = data.get('driver_id', random.randint(1, 10))

        model = load_model()
        prediction = model.predict(X_input)[0]

        # Auto-generate random data for charts
        insert_sample_data(driver_id)

        return jsonify({'eta_minutes': round(prediction, 2)})
    except KeyError as e:
        return jsonify({'error': f'Missing input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Chart endpoints for Metabase
@app.route('/charts/drug-test-trends', methods=['GET'])
def drug_test_trends():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT test_date::date, 
               SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as pass_count,
               SUM(CASE WHEN result = 'fail' THEN 1 ELSE 0 END) as fail_count
        FROM drug_tests
        GROUP BY test_date
        ORDER BY test_date
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@app.route('/charts/drivers-over-3-violations', methods=['GET'])
def drivers_over_3_violations():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT driver_id, COUNT(*) as violation_count
        FROM violations
        GROUP BY driver_id
        HAVING COUNT(*) > 3
        ORDER BY violation_count DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@app.route('/charts/credential-validity', methods=['GET'])
def credential_validity():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT credential_type,
               SUM(CASE WHEN valid = true THEN 1 ELSE 0 END) as valid_count,
               SUM(CASE WHEN valid = false THEN 1 ELSE 0 END) as invalid_count
        FROM credentials
        GROUP BY credential_type
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@app.route('/charts/monthly-infractions', methods=['GET'])
def monthly_infractions():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE_TRUNC('month', date) as month,
               type,
               COUNT(*) as infraction_count
        FROM violations
        GROUP BY month, type
        ORDER BY month, type
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

# Root route
@app.route('/')
def index():
    return jsonify({"message": "ML Prediction API with chart endpoints & sample data logging."})

if __name__ == '__main__':
    if not os.path.exists(MODEL_PATH):
        train_model()
    app.run(host='0.0.0.0', port=5000)
