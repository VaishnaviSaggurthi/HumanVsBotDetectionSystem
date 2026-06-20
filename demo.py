"""
Bot Detection Demo
------------------
Run this AFTER opening http://localhost:8000 in your browser.
It hijacks the browser's active session to trigger bot detection,
which will lock the frontend with the block overlay.

Steps:
1. Open http://localhost:8000 in browser
2. Open browser console (F12)
3. Run: copy(window.behaviorTracker.sessionId)
4. Paste the session ID when prompted below
5. Watch the browser get blocked!
"""

import requests
import json
import time
import random

API_URL = "http://localhost:5000/api/analyze"

def simulate_bot_on_session(session_id):
    """Send bot-like behavior using the browser's active session ID"""
    bot_data = {
        "sessionId": session_id,
        "timeOnPage": random.uniform(2, 5),
        "totalMouseMovements": random.randint(3, 8),
        "totalClicks": random.randint(20, 30),
        "totalScrollEvents": random.randint(25, 35),
        "totalKeystrokes": 0,
        "avgMouseSpeed": random.uniform(1200, 1800),
        "mouseSpeedVariance": random.uniform(50, 150),
        "avgTimeBetweenMoves": random.uniform(10, 20),
        "straightLineRatio": random.uniform(0.95, 0.99),
        "avgClickInterval": random.uniform(60, 120),
        "clickIntervalVariance": random.uniform(20, 80),
        "avgScrollSpeed": random.uniform(800, 1100),
        "scrollDirection": random.uniform(0.92, 0.99),
        "doubleClickCount": 0
    }

    try:
        response = requests.post(API_URL, json=bot_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"\n[RESULT] Prediction : {result.get('prediction', 'N/A').upper()}")
            print(f"         Confidence : {result.get('confidence', 0):.3f}")
            print(f"         Risk Score : {result.get('riskScore', 0):.3f}")
            print(f"         Blocked    : {result.get('blocked', False)}")
            if result.get('blocked'):
                print(f"         Block Time : {result.get('blockDuration', 0)} seconds")
                print(f"\n[ACTION] Browser frontend is now LOCKED for {result.get('blockDuration', 0)} seconds!")
                print(f"         Check http://localhost:8000 - it should show the block overlay.")
            return result
        else:
            print(f"[ERROR] API returned {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Backend not running. Start with: .\\start_backend.bat")
    except Exception as e:
        print(f"[ERROR] {e}")
    return None


def simulate_human_session():
    """Simulate a clean human session with a new session ID"""
    session_id = f"human_session_{random.randint(1000, 9999)}"
    human_data = {
        "sessionId": session_id,
        "timeOnPage": random.uniform(40, 120),
        "totalMouseMovements": random.randint(120, 300),
        "totalClicks": random.randint(3, 12),
        "totalScrollEvents": random.randint(5, 20),
        "totalKeystrokes": random.randint(10, 40),
        "avgMouseSpeed": random.uniform(150, 350),
        "mouseSpeedVariance": random.uniform(3000, 8000),
        "avgTimeBetweenMoves": random.uniform(80, 160),
        "straightLineRatio": random.uniform(0.1, 0.45),
        "avgClickInterval": random.uniform(700, 1600),
        "clickIntervalVariance": random.uniform(35000, 80000),
        "avgScrollSpeed": random.uniform(200, 500),
        "scrollDirection": random.uniform(-0.2, 0.4),
        "doubleClickCount": random.randint(0, 3)
    }
    try:
        response = requests.post(API_URL, json=human_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            correct = result.get('prediction') == 'human'
            status = "[CORRECT]" if correct else "[WRONG]"
            print(f"  {status} {session_id} -> {result.get('prediction','N/A').upper()} (conf: {result.get('confidence',0):.2f})")
            return correct
    except:
        print("  [ERROR] Could not reach API")
    return False


def simulate_bot_session():
    """Simulate a bot session with a new session ID"""
    session_id = f"bot_session_{random.randint(1000, 9999)}"
    bot_data = {
        "sessionId": session_id,
        "timeOnPage": random.uniform(2, 8),
        "totalMouseMovements": random.randint(3, 10),
        "totalClicks": random.randint(18, 30),
        "totalScrollEvents": random.randint(20, 35),
        "totalKeystrokes": 0,
        "avgMouseSpeed": random.uniform(1100, 1800),
        "mouseSpeedVariance": random.uniform(50, 200),
        "avgTimeBetweenMoves": random.uniform(10, 25),
        "straightLineRatio": random.uniform(0.93, 0.99),
        "avgClickInterval": random.uniform(60, 130),
        "clickIntervalVariance": random.uniform(20, 100),
        "avgScrollSpeed": random.uniform(750, 1100),
        "scrollDirection": random.uniform(0.90, 0.99),
        "doubleClickCount": 0
    }
    try:
        response = requests.post(API_URL, json=bot_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            correct = result.get('prediction') == 'bot'
            status = "[CORRECT]" if correct else "[WRONG]"
            print(f"  {status} {session_id} -> {result.get('prediction','N/A').upper()} (conf: {result.get('confidence',0):.2f}, blocked: {result.get('blocked',False)})")
            return correct
    except:
        print("  [ERROR] Could not reach API")
    return False


def main():
    print("=" * 55)
    print("       Bot Detection System - Demo")
    print("=" * 55)
    print()
    print("Choose an option:")
    print("  1. Trigger bot block on YOUR browser session")
    print("  2. Run accuracy test (human + bot simulations)")
    print()
    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        print()
        print("Steps to get your browser session ID:")
        print("  1. Open http://localhost:8000 in your browser")
        print("  2. Press F12 -> Console tab")
        print("  3. Type: window.behaviorTracker.sessionId")
        print("  4. Copy the value shown")
        print()
        session_id = input("Paste your browser session ID here: ").strip()

        if not session_id:
            print("[ERROR] No session ID provided.")
            return

        print(f"\nSending bot behavior for session: {session_id}")
        print("Watch your browser at http://localhost:8000 ...")
        print()

        result = simulate_bot_on_session(session_id)

        if result and result.get('blocked'):
            print()
            print("=" * 55)
            print("  BROWSER IS NOW BLOCKED!")
            print(f"  Countdown: {result.get('blockDuration', 35)} seconds")
            print("  Check http://localhost:8000 for the block overlay")
            print("=" * 55)
        elif result and result.get('prediction') == 'bot':
            print()
            print("[INFO] Bot detected but risk score below block threshold.")
            print("       Session is being monitored.")

    elif choice == "2":
        print()
        print("Running accuracy test with 5 human + 5 bot sessions...")
        print()

        print("Human Sessions:")
        print("-" * 40)
        human_correct = sum(simulate_human_session() for _ in range(5))

        print()
        print("Bot Sessions:")
        print("-" * 40)
        bot_correct = sum(simulate_bot_session() for _ in range(5))

        total = human_correct + bot_correct
        print()
        print("=" * 40)
        print(f"Human Accuracy : {human_correct}/5 ({human_correct*20}%)")
        print(f"Bot Accuracy   : {bot_correct}/5 ({bot_correct*20}%)")
        print(f"Overall        : {total}/10 ({total*10}%)")
        print("=" * 40)

        if total >= 8:
            print("System is working well!")
        else:
            print("System needs tuning.")
    else:
        print("[ERROR] Invalid choice. Enter 1 or 2.")


if __name__ == "__main__":
    main()
