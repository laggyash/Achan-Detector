import os
import json
import cv2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from ultralytics import YOLO

# --- Configuration ---
MODEL = YOLO("yolov8n.pt")
VIDEO_PATH = "myvideo.mp4"
EXIT_BOX_FILE = "exit_point.json"
GOOGLE_MAPS_API_KEY = "AIzaSyDNYydMU9ms87z6oZf30c0SCjxBTAOkz8g"  # IMPORTANT: Replace with your key

# --- FastAPI App Initialization ---
app = FastAPI(title="Achan Detector API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- Detection Logic ---
try:
    with open(EXIT_BOX_FILE) as f:
        data = json.load(f)
        exit_point = tuple(data["exit_point"])
except FileNotFoundError:
    print(f"Error: '{EXIT_BOX_FILE}' not found. Please run define_exitpoint.py first.")
    exit_point = (0, 0, 1, 1) # Default to a tiny box to prevent errors

def at_exit_point(box, threshold=0.5):
    """Checks if a detected object's bounding box overlaps with the exit point."""
    x1, y1, x2, y2 = map(int, box)
    gx1, gy1, gx2, gy2 = exit_point
    ix1, iy1 = max(x1, gx1), max(y1, gy1)
    ix2, iy2 = min(x2, gx2), min(y2, gy2)
    inter_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    box_area = (x2 - x1) * (y2 - y1)
    return box_area > 0 and (inter_area / box_area) > threshold

def get_departure_time(video_path: str) -> float | None:
    """
    Analyzes the video to find the timestamp of the first frame
    where a vehicle is detected at the exit point.
    Returns the timestamp in seconds, or None if no departure is detected.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    departure_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        if frame_count % 5 != 0:  # Process every 5th frame for performance
            continue

        results = MODEL(frame, verbose=False)
        for r in results:
            if r.boxes is None: continue
            for box, cls_id in zip(r.boxes.xyxy, r.boxes.cls):
                if MODEL.names[int(cls_id)] in ["car", "motorcycle", "truck", "bus"]:
                    if at_exit_point(box):
                        departure_frame = frame_count
                        break
            if departure_frame:
                break
    cap.release()

    if departure_frame and fps > 0:
        departure_time = departure_frame / fps
        print(f"[Detection] Departure detected at {departure_time:.2f} seconds.")
        return departure_time
    
    print("[Detection] No departure detected in the video.")
    return None

# --- API Endpoints ---
departure_info_cache = None

@app.get("/departure-info")
def get_departure_info():
    """
    Endpoint to get the departure time from the video.
    Caches the result after the first calculation.
    """
    global departure_info_cache
    if departure_info_cache is None:
        print("Calculating departure time for the first time...")
        departure_time = get_departure_time(VIDEO_PATH)
        departure_info_cache = {"departure_time": departure_time}
    return departure_info_cache

@app.get("/status/eta")
def eta():
    """Endpoint to get ETA from Google Maps."""
    origin = "Ernakulam Metro Station, Kochi"
    destination = "MITS College, Varikoli"
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={GOOGLE_MAPS_API_KEY}"
    try:
        resp = requests.get(url)
        data = resp.json()
        if data["status"] == "OK":
            route = data["routes"][0]["legs"][0]
            return {"eta": route["duration"]["text"], "distance": route["distance"]["text"], "origin": origin, "destination": destination}
    except requests.RequestException as e:
        print(f"Error calling Google Maps API: {e}")
    return {"eta": "N/A", "distance": "N/A", "origin": origin, "destination": destination}
