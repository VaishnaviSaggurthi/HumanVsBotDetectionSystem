from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import numpy as np
from datetime import datetime, timedelta
import joblib
import os
import sys
import random
sys.path.append('..')
from ml_model.bot_classifier import BotClassifier

app = Flask(__name__)
CORS(app)

class BotDetectionAPI:
    def __init__(self):
        self.db_path = 'data/interactions.db'
        self.model_path = 'ml_model/bot_classifier.pkl'
        self.classifier = None
        self.flagged_devices = {}
        self.blocked_sessions = {}  # sessionId -> unblock_datetime

        self.init_database()
        self.load_or_train_model()

    def init_database(self):
        os.makedirs('data', exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT, features TEXT, prediction TEXT,
            confidence REAL, risk_score REAL, timestamp DATETIME,
            is_blocked BOOLEAN DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT, alert_type TEXT, message TEXT,
            device_info TEXT, ip_address TEXT,
            timestamp DATETIME, severity TEXT DEFAULT 'MEDIUM')''')
        c.execute('''CREATE TABLE IF NOT EXISTS flagged_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE, ip_address TEXT, flag_reason TEXT,
            bot_count INTEGER DEFAULT 1, first_detected DATETIME,
            last_detected DATETIME, is_blocked BOOLEAN DEFAULT 0)''')
        conn.commit()
        conn.close()

    def load_or_train_model(self):
        if os.path.exists(self.model_path):
            model_data = joblib.load(self.model_path)
            class ScaledRF:
                def __init__(self, scaler, model):
                    self.scaler = scaler
                    self.model = model
                def predict_proba(self, X):
                    return self.model.predict_proba(self.scaler.transform(X))
                def predict(self, X):
                    return self.model.predict(self.scaler.transform(X))
            self.classifier = ScaledRF(model_data['scaler'], model_data['model'])
        else:
            bc = BotClassifier()
            trained = bc.train_model()
            os.makedirs('ml_model', exist_ok=True)
            joblib.dump({'scaler': trained.scaler, 'model': trained.model,
                         'feature_names': bc.feature_names}, self.model_path)
            self.classifier = trained

    def extract_features(self, data):
        return np.array([
            data.get('timeOnPage', 0),
            data.get('totalMouseMovements', 0),
            data.get('totalClicks', 0),
            data.get('totalScrollEvents', 0),
            data.get('avgMouseSpeed', 0),
            data.get('mouseSpeedVariance', 0),
            data.get('avgTimeBetweenMoves', 0),
            data.get('straightLineRatio', 0),
            data.get('avgClickInterval', 0),
            data.get('clickIntervalVariance', 0),
            data.get('avgScrollSpeed', 0),
            data.get('scrollDirection', 0),
            data.get('doubleClickCount', 0)
        ]).reshape(1, -1)

    def calculate_risk_score(self, prediction, confidence, features):
        base_risk = confidence if prediction == 'bot' else (1 - confidence)
        extra = 0
        if features[4] > 1000:  extra += 0.2   # fast mouse
        if features[7] > 0.95:  extra += 0.3   # straight lines
        if features[9] < 100:   extra += 0.2   # regular clicks
        if features[1] == 0 and features[2] > 0: extra += 0.4  # no mouse + clicks
        return min(1.0, base_risk + extra)

    def is_blocked(self, session_id):
        if session_id in self.blocked_sessions:
            unblock_time = self.blocked_sessions[session_id]
            if datetime.now() < unblock_time:
                remaining = int((unblock_time - datetime.now()).total_seconds())
                return True, remaining
            else:
                del self.blocked_sessions[session_id]
        return False, 0

    def block_session(self, session_id):
        duration = random.randint(30, 40)
        self.blocked_sessions[session_id] = datetime.now() + timedelta(seconds=duration)
        return duration

    def flag_device(self, device_id, ip_address, reason):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT id FROM flagged_devices WHERE device_id = ?', (device_id,))
        if c.fetchone():
            c.execute('''UPDATE flagged_devices SET bot_count = bot_count + 1,
                last_detected = ?, flag_reason = ? WHERE device_id = ?''',
                (datetime.now(), reason, device_id))
        else:
            c.execute('''INSERT INTO flagged_devices
                (device_id, ip_address, flag_reason, first_detected, last_detected)
                VALUES (?, ?, ?, ?, ?)''',
                (device_id, ip_address, reason, datetime.now(), datetime.now()))
        conn.commit()
        conn.close()
        self.flagged_devices[device_id] = ip_address

    def log_alert(self, session_id, alert_type, message, device_id, ip_address, severity):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO alerts
            (session_id, alert_type, message, device_info, ip_address, timestamp, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (session_id, alert_type, message, device_id, ip_address, datetime.now(), severity))
        conn.commit()
        conn.close()
        print(f"[ADMIN ALERT] [{severity}] {alert_type} | {message} | IP: {ip_address}")

    def store_interaction(self, session_id, data, prediction, confidence, risk_score):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO interactions
            (session_id, features, prediction, confidence, risk_score, timestamp, is_blocked)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (session_id, json.dumps(data), prediction, confidence,
             risk_score, datetime.now(), prediction == 'bot'))
        conn.commit()
        conn.close()


bot_api = BotDetectionAPI()


@app.route('/api/check_block', methods=['GET'])
def check_block():
    """Check if a session is currently blocked - called on every page load"""
    session_id = request.args.get('sessionId', '')
    blocked, remaining = bot_api.is_blocked(session_id)
    return jsonify({'blocked': blocked, 'remaining': remaining})


@app.route('/api/analyze', methods=['POST'])
def analyze_behavior():
    try:
        data = request.json
        session_id = data.get('sessionId', 'unknown')
        client_ip = request.remote_addr
        device_id = f"{client_ip}_{session_id.split('_')[0]}"

        # Check if already blocked
        blocked, remaining = bot_api.is_blocked(session_id)
        if blocked:
            print(f"[BLOCKED] Session {session_id} tried to access - {remaining}s remaining")
            return jsonify({
                'sessionId': session_id,
                'prediction': 'bot',
                'confidence': 1.0,
                'riskScore': 1.0,
                'blocked': True,
                'blockRemaining': remaining,
                'securityResponses': ['BLOCKED'],
                'timestamp': datetime.now().isoformat()
            })

        # Run ML prediction
        features = bot_api.extract_features(data)
        proba = bot_api.classifier.predict_proba(features)[0]
        prediction = 'bot' if proba[1] > 0.5 else 'human'
        confidence = float(max(proba))
        risk_score = bot_api.calculate_risk_score(prediction, confidence, features[0])

        blocked_now = False
        block_duration = 0
        security_responses = []

        if prediction == 'bot':
            # Flag device
            bot_api.flag_device(device_id, client_ip, f"Bot - Risk: {risk_score:.2f}")

            if risk_score > 0.8:
                # Block for 30-40 seconds
                block_duration = bot_api.block_session(session_id)
                blocked_now = True
                security_responses.append('BLOCKED')
                bot_api.log_alert(session_id, 'BOT_BLOCKED',
                    f"Bot blocked for {block_duration}s | Risk: {risk_score:.2f}",
                    device_id, client_ip, 'HIGH')
                print(f"[BOT BLOCKED] Session {session_id} blocked for {block_duration}s | Risk: {risk_score:.2f} | IP: {client_ip}")
            else:
                security_responses.append('MONITORED')
                bot_api.log_alert(session_id, 'BOT_DETECTED',
                    f"Bot detected | Risk: {risk_score:.2f}",
                    device_id, client_ip, 'MEDIUM')
        elif risk_score > 0.6:
            security_responses.append('MONITORED')
        else:
            security_responses.append('ALLOWED')

        bot_api.store_interaction(session_id, data, prediction, confidence, risk_score)

        return jsonify({
            'sessionId': session_id,
            'prediction': prediction,
            'confidence': confidence,
            'riskScore': risk_score,
            'blocked': blocked_now,
            'blockDuration': block_duration,
            'blockRemaining': block_duration,
            'securityResponses': security_responses,
            'deviceFlagged': device_id in bot_api.flagged_devices,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = sqlite3.connect(bot_api.db_path)
        c = conn.cursor()

        c.execute('''SELECT prediction, COUNT(*), AVG(confidence), AVG(risk_score)
            FROM interactions WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY prediction''')
        interaction_stats = c.fetchall()

        c.execute('''SELECT alert_type, severity, COUNT(*) FROM alerts
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY alert_type, severity''')
        alert_stats = c.fetchall()

        c.execute('''SELECT device_id, ip_address, flag_reason, bot_count,
            first_detected, last_detected, is_blocked
            FROM flagged_devices ORDER BY last_detected DESC''')
        flagged_devices = c.fetchall()

        c.execute('''SELECT session_id, alert_type, message, device_info,
            ip_address, timestamp, severity FROM alerts
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC LIMIT 20''')
        recent_alerts = c.fetchall()

        c.execute('''SELECT strftime('%H', timestamp), prediction, COUNT(*)
            FROM interactions WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY strftime('%H', timestamp), prediction
            ORDER BY strftime('%H', timestamp)''')
        hourly_trends = c.fetchall()

        conn.close()
        return jsonify({
            'interactionStats': interaction_stats,
            'alertStats': alert_stats,
            'flaggedDevices': flagged_devices,
            'recentAlerts': recent_alerts,
            'hourlyTrends': hourly_trends
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
