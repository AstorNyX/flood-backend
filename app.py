from fastapi import FastAPI
import pickle
import numpy as np
import requests

app = FastAPI()

model = pickle.load(open("model.pkl", "rb"))

TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "-1003989233809"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

@app.post("/predict")
def predict(data: dict):
    try:
        water = data["water_level"]
        rain = data["rain_intensity"]

        features = np.array([[water, rain]])
        state = int(model.predict(features)[0])

        if state >= 2:
            send_telegram(f"⚠ TEST ALERT\nState: {state}\nWater: {water}\nRain: {rain}")

        return {"state": state}

    except Exception as e:
        print("ERROR:", e)
        return {"state": 0}

@app.get("/")
def home():
    return {"status": "running"}