from fastapi import FastAPI
import pickle
import numpy as np
import requests

app = FastAPI()

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== TELEGRAM CONFIG (HARDCODED FOR NOW) =====
TOKEN = "8573374564:AAFmOnDbMd1r2DVJbKtIs03gnj-b6yY6D98"
CHAT_ID = "-1003989233809"

# ===== STORE LAST DATA =====
last_data = {
    "water": 0,
    "rain": 0,
    "state": 0
}

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
        print("Telegram response:", res.text)
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
    water = data["water_level"]
    rain = data["rain_intensity"]

    # ===== MODEL =====
    features = np.array([[water, rain]])
    state = int(model.predict(features)[0])

    # ===== SAVE LAST DATA =====
    last_data["water"] = water
    last_data["rain"] = rain
    last_data["state"] = state

    print("STATE:", state)

    # ===== TELEGRAM TRIGGER =====
    if state >= 2:
        print("Sending Telegram message...")
        msg = f"""⚠ FLOOD ALERT

State: {state}
Water Level: {water}
Rain Intensity: {rain}
"""
        send_telegram(msg)

    return {"state": state}