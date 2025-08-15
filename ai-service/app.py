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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

# -------------------- ML MODEL --------------------
MODEL_PATH = 'model.pkl'

def train_model():
    try:
        X = np.array([[1, 1], [2, 2], [3, 1.5], [4, 3]])
        y = np.array([10, 20, 22, 35])
        model = LinearRegression().fit(X, y)
        joblib.dump(model, MODEL_PATH)
        logging.info("Model trained and saved to disk.")
    except Exception as e:
        logging.error(f"Error training model: {e}")

def load_model():
    try:
        if not os.path.exists(MODEL_PATH):
            logging.info("Model not found, training a new one...")
            train_model()
        return joblib.load(MODEL_PATH)
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        return None

# -------------------- SAMPLE DATA INSERT --------------------
def insert_sample_data(driver_id):
    conn = None
    try:
        conn = get_db_conn()
        if conn is None:
            logging.error("No database connection available.")
            return

        cur = conn.cursor()
        # Random drug test
        test_result = random.choice(['pass', 'fail'])
        cur.execute("""
            INSERT INTO drug_tests (driver_id, result, test_date)
            VALUES (%s, %s, %s)
        """, (driver_id, test_result, datetime.now().date()))

        # Random violation
        if random.random() < 0.5:
            violation_type = random.choice(['speeding', 'dui', 'reckless driving'])
            cur.execute("""
                INSERT INTO violations (driver_id, type, description, date)
                VALUES (%s, %s, %s, %s)
            """, (driver_id, violation_type, f"{violation_type} violation", datetime.now().date()))

        # Random credential check
        credential_type = random.choice(['license', 'medical', 'training'])
        valid = random.choice([True, False])
        cur.execute("""
            INSERT INTO credentials (driver_id, credential_type, valid, remarks, check_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (driver_id, credential_type, valid, "Auto-generated", datetime.now().date()))

        conn.commit()
        logging.info(f"Sample data inserted for driver {driver_id}")
    except Exception as e:
        logging.error(f"Error inserting sample data: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

# -------------------- NEW ROUTES --------------------
@app.route('/api/drivers', methods=['POST'])
def create_driver():
    """Register a new driver"""
    data = request.get_json()
    conn = get_db_conn()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO drivers (name, license_number, contact, birthdate)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (data['name'], data['license_number'], data['contact'], data.get('birthdate', datetime.now().date())))
        driver_id = cur.fetchone()['id']
        conn.commit()
        return jsonify({"message": "Driver created", "driver_id": driver_id}), 201
    except Exception as e:
        conn.rollback()
        logging.error(f"Error creating driver: {e}")
        return jsonify({"error": "Failed to create driver"}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/drivers/<int:driver_id>/profile', methods=['GET'])
def get_driver_profile(driver_id):
    """Get driver profile + related records"""
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'No database connection.'}), 500

    try:
        cur = conn.cursor()

        cur.execute("SELECT id, name, license_number, contact FROM drivers WHERE id = %s", (driver_id,))
        driver = cur.fetchone()
        if not driver:
            return jsonify({'error': 'Driver not found'}), 404

        cur.execute("SELECT id, rating, content FROM feedback WHERE driver_id = %s", (driver_id,))
        feedback = cur.fetchall()

        cur.execute("SELECT id, type, description, date FROM violations WHERE driver_id = %s", (driver_id,))
        violations = cur.fetchall()

        cur.execute("SELECT id, incident, description, date FROM infractions WHERE driver_id = %s", (driver_id,))
        infractions = cur.fetchall()

        cur.execute("SELECT id, test_date, result FROM drug_tests WHERE driver_id = %s", (driver_id,))
        drug_tests = cur.fetchall()

        cur.execute("SELECT id, credential_type AS type, valid AS is_valid, remarks FROM credentials WHERE driver_id = %s", (driver_id,))
        credentials = cur.fetchall()

        return jsonify({
            "id": driver["id"],
            "name": driver["name"],
            "license_number": driver["license_number"],
            "contact": driver["contact"],
            "feedback": feedback,
            "violations": violations,
            "infractions": infractions,
            "drug_test_results": drug_tests,
            "credentials": credentials
        })
    except Exception as e:
        logging.error(f"Error fetching driver profile: {e}")
        return jsonify({'error': 'Server error'}), 500
    finally:
        cur.close()
        conn.close()

# -------------------- PREDICT + CHART ROUTES --------------------
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)
        X_input = [[data['distance_km'], data['fuel_used']]]
        driver_id = data.get('driver_id', random.randint(1, 10))

        model = load_model()
        if model is None:
            return jsonify({'error': 'Model not loaded.'}), 500

        prediction = model.predict(X_input)[0]
        insert_sample_data(driver_id)

        return jsonify({'eta_minutes': round(prediction, 2)})
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return jsonify({"message": "ML Prediction API with chart endpoints & driver profile."})

if __name__ == '__main__':
    if not os.path.exists(MODEL_PATH):
        train_model()
    if get_db_conn() is None:
        logging.error("Failed to connect to the database. Exiting.")
        exit(1)
    app.run(host='0.0.0.0', port=5000, debug=False)
