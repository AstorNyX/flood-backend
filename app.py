from fastapi import FastAPI
import pickle
import numpy as np
import requests
import time

app = FastAPI()

model = pickle.load(open("model.pkl", "rb"))

TOKEN = "8573374564:AAFv1x4VYdewYM2cFJF5JEX1YugV3jlFyyw"
CHAT_ID = "-1003989233809"

last_state = -1
last_sent_time = 0

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

@app.post("/predict")
def predict(data: dict):
    global last_state, last_sent_time

    water = data["water_level"]
    rain = data["rain_intensity"]

    features = np.array([[water, rain]])
    state = int(model.predict(features)[0])

    print("STATE:", state)

    # anti-spam logic
    if state >= 2:
        if state != last_state or (time.time() - last_sent_time > 60):
            msg = f"""⚠ FLOOD ALERT

State: {state}
Water: {water}
Rain: {rain}
"""
            send_telegram(msg)
            last_sent_time = time.time()

    last_state = state

    return {"state": state}

@app.get("/")
def home():
    return {"status": "running"}