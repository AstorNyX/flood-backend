from fastapi import FastAPI
import pickle
import numpy as np
import requests

app = FastAPI()

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== TELEGRAM CONFIG =====
TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "-1003989233809"

# ===== STORE LAST DATA =====
last_data = {
    "water": 0,
    "rain": 0,
    "state": 0
}

# ===== CONTROL VARIABLES =====
last_alert_state = -1

# ===== LABEL FUNCTION =====
def get_label(state):
    labels = ["SAFE", "LOW", "MODERATE", "HIGH", "CRITICAL"]
    return labels[state] if state < len(labels) else "UNKNOWN"

# ===== TELEGRAM FUNCTION =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    try:
        res = requests.post(url, data=data, timeout=5)
        print("Telegram status:", res.status_code)
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
    global last_alert_state

    water = data["water_level"]
    rain = data["rain_intensity"]

    # ===== MODEL =====
    features = np.array([[water, rain]])
    state = int(model.predict(features)[0])

    # ===== SAVE LAST DATA =====
    last_data["water"] = water
    last_data["rain"] = rain
    last_data["state"] = state

    print(f"STATE: {state}")

    # ===== TELEGRAM ALERT (NO SPAM) =====
    if state >= 2 and state != last_alert_state:
        print("Sending Telegram alert...")

        msg = f"""⚠ FLOOD ALERT

Level: {get_label(state)}
State: {state}

Water Level: {water}
Rain Intensity: {rain}
"""
        send_telegram(msg)

    last_alert_state = state

    return {"state": state}