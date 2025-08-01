from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only. Restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_MAPS_API_KEY = "AIzaSyDNYydMU9ms87z6oZf30c0SCjxBTAOkz8g"  # <-- Replace with your real key

@app.get("/status/father-inside")
def father_inside():
    # For prototype, always return True
    return {"inside": True}

@app.get("/status/father-gone")
def father_gone():
    # For prototype, always return True (simulate "gone out")
    return {"gone": True}

@app.get("/status/eta")
def eta():
    origin = "Ernakulam Metro Station, Kochi"
    destination = "MITS College, Varikoli"
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origin}&destination={destination}&mode=driving&departure_time=now&key={GOOGLE_MAPS_API_KEY}"
    )
    resp = requests.get(url)
    data = resp.json()
    print(data)
    if data["status"] == "OK":
        route = data["routes"][0]["legs"][0]
        eta_val = route["duration"]["text"]
        distance_val = route["distance"]["text"]
        print(f"ETA: {eta_val} | Distance: {distance_val}")  # Print to terminal
        return {
            "eta": eta_val,
            "distance": distance_val,
            "origin": origin,
            "destination": destination
        }
    else:
        print("ETA: N/A | Distance: N/A")
        return {
            "eta": "N/A",
            "distance": "N/A",
            "origin": origin,
            "destination": destination
            }