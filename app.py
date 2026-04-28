from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "running"}

@app.post("/predict")
def predict(data: dict):
    wl = data["water_level"]
    rain = data["rain_intensity"]

    if wl > 30:
        state = 2
    elif wl > 20:
        state = 1
    else:
        state = 0

    return {"state": state}