from fastapi import FastAPI
import pickle
import numpy as np
import requests
import os

app = FastAPI()

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))
# ===== TELEGRAM CONFIG =====
TOKEN = os.getenv("8573374564:AAFmOnDbMd1r2DVJbKtIs03gnj-b6yY6D98")     # set in Render
CHAT_ID = os.getenv("-1003989233809")     # set in Render

last_state = -1   # prevents spam

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    try:
        requests.post(url, data=data, timeout=5)
    except:
        pass


# ===== ROUTES =====
@app.get("/")
def home():
    return {"status": "running"}


@app.post("/predict")
def predict(data: dict):
    global last_state

    water = data["water_level"]
    rain = data["rain_intensity"]

    # ===== MODEL =====
    features = np.array([[water, rain]])
    state = int(model.predict(features)[0])

    # ===== TELEGRAM TRIGGER =====
    if state >= 2 and state != last_state:
        msg = f"""⚠ FLOOD ALERT

State: {state}
Water Level: {water}
Rain Intensity: {rain}
"""
        send_telegram(msg)

    last_state = state

    return {"state": state}