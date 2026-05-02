from fastapi import FastAPI
import pickle
import numpy as np
import requests

app = FastAPI()

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== TELEGRAM CONFIG =====
TOKEN = "8573374564:AAFv1x4VYdewYM2cFJF5JEX1YugV3jlFyyw"
CHAT_ID = "-1003989233809"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    try:
        r = requests.post(url, data=data, timeout=5)
        print("TG STATUS:", r.status_code)
        print("TG RESPONSE:", r.text)
    except Exception as e:
        print("TG ERROR:", e)


@app.get("/")
def home():
    return {"status": "running"}


@app.post("/predict")
def predict(data: dict):
    try:
        water = data["water_level"]
        rain = data["rain_intensity"]

        features = np.array([[water, rain]])
        state = int(model.predict(features)[0])

        print("STATE:", state)

        # ⭐ FORCE TELEGRAM FOR TESTING
        if state >= 2:
            msg = f"""⚠ TEST ALERT

State: {state}
Water: {water}
Rain: {rain}
"""
            send_telegram(msg)

        return {"state": state}

    except Exception as e:
        print("ERROR:", e)
        return {"state": 0}