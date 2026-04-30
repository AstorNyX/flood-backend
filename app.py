from fastapi import FastAPI
import pickle
import numpy as np

app = FastAPI()

model = pickle.load(open("model.pkl", "rb"))

@app.get("/")
def home():
    return {"status": "running"}

@app.post("/predict")
def predict(data: dict):
    wl = data["water_level"]
    rain = data["rain_intensity"]

    input_data = np.array([[wl, rain]])

    prediction = model.predict(input_data)[0]

    return {"state": int(prediction)}