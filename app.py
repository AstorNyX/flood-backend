from fastapi import FastAPI
import pickle
import numpy as np
import requests
import time
import json
import threading
import paho.mqtt.client as mqtt

app = FastAPI()

# ===== LOAD MODEL =====
model = pickle.load(open("model.pkl", "rb"))

# ===== TELEGRAM CONFIG =====
TOKEN   = "8573374564:AAFmOnDbMd1r2DVJbKtIs03gnj-b6yY6D98"
CHAT_ID = "-1003989233809"

# ===== MQTT CONFIG =====
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT   = 1883
MQTT_TOPIC  = "flood/sensors"          # ESP32 publishes here

# ===== STATE STORAGE =====
last_data = {"water": 0, "rain": 0, "state": 0}

last_alert_state = -1
last_water       = -1
last_rain        = -1
last_sent_time   = 0

# ===== SETTINGS =====
WATER_DELTA  = 2
RAIN_DELTA   = 50
COOLDOWN_SEC = 10

# ===== HELPERS =====
def get_label(state):
    labels = ["SAFE", "LOW", "MODERATE", "HIGH", "CRITICAL"]
    return labels[state] if state < len(labels) else "UNKNOWN"

def get_emoji(state):
    emojis = ["✅", "🟡", "🟠", "🔴", "🆘"]
    return emojis[state] if state < len(emojis) else "❓"

def send_telegram(msg):
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=8)
        print(f"[Telegram] {res.status_code}")
    except Exception as e:
        print(f"[Telegram] Error: {e}")

def run_prediction(water, rain):
    """Shared prediction logic used by both MQTT and HTTP paths."""
    global last_alert_state, last_water, last_rain, last_sent_time

    features = np.array([[water, rain]])
    state    = int(model.predict(features)[0])

    last_data["water"] = water
    last_data["rain"]  = rain
    last_data["state"] = state

    print(f"[PREDICT] State={state} ({get_label(state)}) | Water={water} | Rain={rain}")

    water_changed = abs(water - last_water) > WATER_DELTA
    rain_changed  = abs(rain  - last_rain)  > RAIN_DELTA
    state_changed = state != last_alert_state

    now      = time.time()
    can_send = (now - last_sent_time) > COOLDOWN_SEC

    if state >= 2 and can_send and (state_changed or water_changed or rain_changed):
        print("[Telegram] Sending ALERT...")
        msg = (
            f"{get_emoji(state)} <b>FLOOD ALERT — {get_label(state)}</b>\n\n"
            f"🌊 Water Level   : {water} cm\n"
            f"🌧 Rain Intensity: {rain}\n"
            f"📊 State Code    : {state}\n"
            f"📡 Source        : {'MQTT' if True else 'HTTP'}"
        )
        send_telegram(msg)
        last_sent_time = now

    elif state < 2 and last_alert_state >= 2 and can_send:
        print("[Telegram] Sending RECOVERY...")
        msg = (
            f"✅ <b>FLOOD CLEARED — {get_label(state)}</b>\n\n"
            f"🌊 Water Level   : {water} cm\n"
            f"🌧 Rain Intensity: {rain}\n"
            f"📊 State Code    : {state}\n"
        )
        send_telegram(msg)
        last_sent_time = now

    last_alert_state = state
    last_water       = water
    last_rain        = rain

    return state

# ===== MQTT CALLBACKS =====
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Connected to {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
        print(f"[MQTT] Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"[MQTT] Connection failed, rc={rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        water   = payload.get("water_level", 0)
        rain    = payload.get("rain_intensity", 0)
        print(f"[MQTT] Received -> water={water}, rain={rain}")
        run_prediction(water, rain)
    except Exception as e:
        print(f"[MQTT] Parse error: {e}")

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()   # blocking — runs in its own thread

# ===== START MQTT IN BACKGROUND =====
mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

# ===== HTTP ROUTES (kept for manual testing via /docs) =====

@app.get("/")
def home():
    return {"status": "running", "mqtt": f"{MQTT_BROKER}:{MQTT_PORT}/{MQTT_TOPIC}"}

@app.get("/ping")
def ping():
    return {"pong": True, "time": time.time()}

@app.get("/status")
def status():
    return last_data

@app.post("/predict")
def predict(data: dict):
    water = data.get("water_level", 0)
    rain  = data.get("rain_intensity", 0)
    state = run_prediction(water, rain)
    return {"state": state, "label": get_label(state)}
