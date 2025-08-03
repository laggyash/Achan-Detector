import os
import json
import cv2
import shutil
from typing import Tuple, List, Dict
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from ultralytics import YOLO

MODEL = YOLO("yolov8n.pt")
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

VIDEO_PATH = os.path.join(UPLOAD_DIR, "video.mp4")
EXIT_BOX_FILE = "exit_point.json"
CONFIG_FILE = "config.json"

Maps_API_KEY = "AIzaSyDNYydMU9ms87z6oZf30c0SCjxBTAOkz8g" 

app = FastAPI(title="Achan Detector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_config() -> Dict[str, str]:
    """Loads origin/destination config from the JSON file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"origin": "", "destination": ""}

def load_exit_point() -> Tuple[int, int, int, int] | None:
    """Loads exit point coordinates from the JSON file."""
    try:
        with open(EXIT_BOX_FILE, 'r') as f:
            data = json.load(f)
            return tuple(data["exit_point"])
    except (FileNotFoundError, KeyError, IndexError, json.JSONDecodeError):
        return None

def at_exit_point(box: List[float], exit_point: Tuple[int, int, int, int], threshold: float = 0.5) -> bool:
    """Checks if a detected box overlaps significantly with the exit point."""
    if not exit_point: return False
    x1, y1, x2, y2 = map(int, box)
    gx1, gy1, gx2, gy2 = exit_point
    ix1, iy1 = max(x1, gx1), max(y1, gy1)
    ix2, iy2 = min(x2, gx2), min(y2, gy2)
    inter_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    box_area = (x2 - x1) * (y2 - y1)
    return box_area > 0 and (inter_area / box_area) > threshold

def get_departure_time(video_path: str) -> float | None:
    """Analyzes a video to find the departure time of a vehicle."""
    exit_point = load_exit_point()
    if not exit_point:
        print("Warning: Exit point not defined. Cannot calculate departure time.")
        return None

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        print("Warning: Video FPS is 0. Cannot calculate time.")
        cap.release()
        return None
        
    frame_count = 0
    departure_frame = None
    FRAME_SKIP_INTERVAL = 10 
    PROCESSING_SIZE = (640, 480) 

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame_count += 1
        if frame_count % FRAME_SKIP_INTERVAL != 0: continue

        small_frame = cv2.resize(frame, PROCESSING_SIZE)
        results = MODEL(small_frame, verbose=False)
        
        for r in results:
            if r.boxes is None: continue
            for box, cls_id in zip(r.boxes.xyxy, r.boxes.cls):
                if MODEL.names[int(cls_id)] in ["car", "motorcycle", "truck", "bus"]:
                    orig_h, orig_w, _ = frame.shape
                    proc_w, proc_h = PROCESSING_SIZE
                    gx1, gy1, gx2, gy2 = exit_point
                    
                    scaled_exit_point = (
                        int(gx1 * (proc_w / orig_w)), int(gy1 * (proc_h / orig_h)),
                        int(gx2 * (proc_w / orig_w)), int(gy2 * (proc_h / orig_h))
                    )

                    if at_exit_point(box, scaled_exit_point):
                        departure_frame = frame_count
                        break
            if departure_frame: break
    cap.release()

    if departure_frame:
        departure_time = departure_frame / fps
        print(f"[Detection] Departure detected at {departure_time:.2f} seconds.")
        return departure_time
    
    print("[Detection] No departure detected in the video.")
    return None

# --- API Endpoints ---

@app.post("/upload-video")
async def upload_video(video: UploadFile = File(...)):
    """Handles video upload and saves it, overwriting any existing video."""
    try:
        with open(VIDEO_PATH, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        # Invalidate departure time cache by deleting it
        if os.path.exists("departure_time.json"):
            os.remove("departure_time.json")
        return {"message": "Video uploaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video upload failed: {e}")

@app.post("/save-exit-point")
async def save_exit_point(exit_point: str = Form(...)):
    """Saves the exit point coordinates."""
    try:
        coords = json.loads(exit_point)
        if not (isinstance(coords, list) and len(coords) == 4 and all(isinstance(i, (int, float)) for i in coords)):
            raise ValueError("Invalid coordinates format.")
        
        x1, y1, x2, y2 = map(int, coords)
        coords_to_save = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

        with open(EXIT_BOX_FILE, "w") as f:
            json.dump({"exit_point": coords_to_save}, f)
        
        return {"message": "Exit point saved."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error saving exit point: {e}")

@app.post("/save-config")
async def save_config(origin: str = Form(...), destination: str = Form(...)):
    """Saves the origin and destination configuration."""
    try:
        config_data = {"origin": origin, "destination": destination}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f)
        return {"message": "Configuration saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {e}")

@app.get("/departure-info")
def get_departure_info_endpoint():
    """Calculates and returns the departure time, using a simple file cache."""
    # Simple cache file to avoid re-calculating on every page load
    cache_file = "departure_time.json"
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        pass # Cache is invalid or not found, proceed to calculate

    departure_time = get_departure_time(VIDEO_PATH)
    result = {"departure_time": departure_time}
    
    # Save result to cache
    with open(cache_file, 'w') as f:
        json.dump(result, f)
        
    return result

@app.get("/status/eta")
def eta():
    """Provides ETA using the saved origin/destination from Google Maps API."""
    config = load_config()
    origin = config.get("origin")
    destination = config.get("destination")

    if not origin or not destination:
        raise HTTPException(status_code=400, detail="Origin or destination not configured. Please use the setup panel.")

    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={Maps_API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data["status"] == "OK":
            route = data["routes"][0]["legs"][0]
            return {"eta": route["duration"]["text"], "distance": route["distance"]["text"], "origin": origin, "destination": destination}
        else:
            error_message = data.get("error_message", "An unknown error occurred.")
            raise HTTPException(status_code=400, detail=f"Google Maps API Error: {data['status']} - {error_message}")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Could not connect to Google Maps API: {e}")

