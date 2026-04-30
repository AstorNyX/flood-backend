from fastapi import FastAPI
import pickle
import numpy as np
import requests
import time

app = FastAPI()

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== TELEGRAM CONFIG =====
TOKEN = "8573374564:AAFmOnDbMd1r2DVJbKtIs03gnj-b6yY6D98"          # <-- put your token
CHAT_ID = "-1003989233809"

# ===== STATE STORAGE =====
last_data = {"water": 0, "rain": 0, "state": 0}

last_alert_state = -1
last_water = -1
last_rain = -1
last_sent_time = 0

# ===== SETTINGS =====
WATER_DELTA = 2        # sensitivity for water change
RAIN_DELTA = 50        # sensitivity for rain change
COOLDOWN_SEC = 5       # min seconds between messages

# ===== HELPERS =====
def get_label(state):
    labels = ["SAFE", "LOW", "MODERATE", "HIGH", "CRITICAL"]
    return labels[state] if state < len(labels) else "UNKNOWN"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        res = requests.post(url, data=data, timeout=5)
        print("Telegram:", res.status_code)
    except Exception as e:
        print("Telegram error:", e)

# ===== ROUTES =====

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/status")
def status():
    return last_data

@app.post("/predict")
def predict(data: dict):
    global last_alert_state, last_water, last_rain, last_sent_time

    water = data["water_level"]
    rain = data["rain_intensity"]

    # ===== MODEL =====
    features = np.array([[water, rain]])
    state = int(model.predict(features)[0])

    # ===== STORE LAST =====
    last_data["water"] = water
    last_data["rain"] = rain
    last_data["state"] = state

    print(f"STATE: {state}, Water: {water}, Rain: {rain}")

    # ===== CHANGE DETECTION =====
    water_changed = abs(water - last_water) > WATER_DELTA
    rain_changed  = abs(rain  - last_rain)  > RAIN_DELTA
    state_changed = state != last_alert_state

    # ===== COOLDOWN =====
    now = time.time()
    can_send = (now - last_sent_time) > COOLDOWN_SEC

    # ===== TELEGRAM TRIGGER =====
    if state >= 2 and can_send and (state_changed or water_changed or rain_changed):
        print("Sending Telegram alert...")

        msg = f"""⚠ FLOOD UPDATE

Level: {get_label(state)}
State: {state}

Water Level: {water}
Rain Intensity: {rain}
"""
        send_telegram(msg)
        last_sent_time = now

    # ===== UPDATE TRACKERS =====
    last_alert_state = state
    last_water = water
    last_rain = rain

    return {"state": state}