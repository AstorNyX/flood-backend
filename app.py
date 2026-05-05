from fastapi import FastAPI
import pickle
import pandas as pd
import requests
import time

app = FastAPI()

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== TELEGRAM CONFIG =====
TOKEN = "8573374564:AAFv1x4VYdewYM2cFJF5JEX1YugV3jlFyyw"
CHAT_ID = "-1003989233809"

labels = ["Very Safe", "Safe", "Risky", "High Risk", "Dangerous"]

last_state = -1
last_sent_time = 0


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)


@app.get("/")
def home():
    return {"status": "running"}


@app.post("/predict")
def predict(data: dict):
    global last_state, last_sent_time

    try:
        rainfall = float(data["rain_intensity"])
        water = float(data["water_level"])

        # ⭐ EXACT SAME FORMAT AS YOUR WORKING CODE
        new_data = pd.DataFrame(
            [[rainfall, water]],
            columns=["Rainfall_mm", "Water_Level_m"]
        )

        pred = int(model.predict(new_data)[0])
        condition = labels[pred]

        print("INPUT:", rainfall, water)
        print("STATE:", pred, condition)

        # ===== TELEGRAM LOGIC =====
        if pred >= 2:
            if pred != last_state or (time.time() - last_sent_time > 60):
                msg = f"""⚠ FLOOD ALERT

State: {pred} ({condition})
Rain: {rainfall}
Water: {water}
"""
                send_telegram(msg)
                last_sent_time = time.time()

        last_state = pred

        return {"state": pred}

    except Exception as e:
        print("ERROR:", e)
        return {"state": 0}