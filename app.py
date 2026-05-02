from fastapi import FastAPI
import pickle
import numpy as np
import requests
import time

app = FastAPI()

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== TELEGRAM CONFIG =====
TOKEN = "8573374564:AAEy8oRKuk0iK8nQ2tXJNXhJJYXzBg87ixA"
CHAT_ID = "-1003989233809"

# ===== STATE STORAGE =====
last_data = {"water": 0, "rain": 0, "state": 0}

last_alert_state = -1
last_water = -1
last_rain = -1
last_sent_time = 0

# ===== SETTINGS =====
WATER_DELTA = 2        # sensitivity for water level change
RAIN_DELTA = 50        # sensitivity for rain intensity change
COOLDOWN_SEC = 10      # min seconds between messages (increased from 5)

# ===== HELPERS =====
def get_label(state):
    labels = ["SAFE", "LOW", "MODERATE", "HIGH", "CRITICAL"]
    return labels[state] if state < len(labels) else "UNKNOWN"

def get_emoji(state):
    emojis = ["✅", "🟡", "🟠", "🔴", "🆘"]
    return emojis[state] if state < len(emojis) else "❓"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=8)
        print(f"Telegram response: {res.status_code} | {res.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

# ===== ROUTES =====

@app.get("/")
def home():
    return {"status": "running"}

# Keepalive endpoint — ping this from UptimeRobot or similar to prevent cold starts
@app.get("/ping")
def ping():
    return {"pong": True, "time": time.time()}

@app.get("/status")
def status():
    return last_data

@app.post("/predict")
def predict(data: dict):
    global last_alert_state, last_water, last_rain, last_sent_time

    water = data.get("water_level", 0)
    rain  = data.get("rain_intensity", 0)

    # ===== MODEL =====
    features = np.array([[water, rain]])
    state = int(model.predict(features)[0])

    # ===== STORE LAST =====
    last_data["water"] = water
    last_data["rain"]  = rain
    last_data["state"] = state

    print(f"[PREDICT] STATE={state} ({get_label(state)}) | Water={water} | Rain={rain}")

    # ===== CHANGE DETECTION =====
    water_changed = abs(water - last_water) > WATER_DELTA
    rain_changed  = abs(rain  - last_rain)  > RAIN_DELTA
    state_changed = state != last_alert_state

    # ===== COOLDOWN =====
    now      = time.time()
    can_send = (now - last_sent_time) > COOLDOWN_SEC

    # ===== TELEGRAM TRIGGER =====
    # Send alert for state >= 2 (MODERATE and above)
    # Also send a recovery message when dropping back to SAFE/LOW
    should_alert = (
        state >= 2 and can_send and (state_changed or water_changed or rain_changed)
    )
    should_recover = (
        state < 2 and last_alert_state >= 2 and can_send
    )

    if should_alert:
        print(">>> Sending Telegram ALERT...")
        emoji = get_emoji(state)
        msg = (
            f"{emoji} <b>FLOOD ALERT — {get_label(state)}</b>\n\n"
            f"🌊 Water Level  : {water} cm\n"
            f"🌧 Rain Intensity: {rain}\n"
            f"📊 State Code   : {state}\n"
        )
        send_telegram(msg)
        last_sent_time = now

    elif should_recover:
        print(">>> Sending Telegram RECOVERY...")
        msg = (
            f"✅ <b>FLOOD CLEARED — {get_label(state)}</b>\n\n"
            f"🌊 Water Level  : {water} cm\n"
            f"🌧 Rain Intensity: {rain}\n"
            f"📊 State Code   : {state}\n"
        )
        send_telegram(msg)
        last_sent_time = now

    # ===== UPDATE TRACKERS =====
    last_alert_state = state
    last_water = water
    last_rain  = rain

    return {"state": state, "label": get_label(state)}
