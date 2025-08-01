import os
import shutil
import cv2
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

model = YOLO("yolov8n.pt")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Local Vehicle Detection")

def notify(message: str):
    print(message)


def detect_vehicle(video_path: str, debug: bool = True) -> bool:

    cap = cv2.VideoCapture(video_path)
    found_vehicle = False
    frame_count = 0
    detected_objects = []

    os.makedirs("debug_frames", exist_ok=True) if debug else None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 5 != 0: 
            continue

        results = model(frame, verbose=False)

        for r in results:
            for box, cls_id in zip(r.boxes.xyxy, r.boxes.cls):
                cls_name = model.names[int(cls_id)]
                detected_objects.append(cls_name)

                if debug:
                    annotated = r.plot()
                    cv2.imwrite(f"debug_frames/frame_{frame_count}.jpg", annotated)

                if cls_name in ["car", "motorcycle", "truck", "bus"]:
                    found_vehicle = True

        if found_vehicle:
            break

    cap.release()

    if debug:
        print(f"[DEBUG] Frames processed: {frame_count}")
        print(f"[DEBUG] Objects detected: {detected_objects}")

    return found_vehicle

@app.post("/upload-clip")
async def upload_clip(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        vehicle_present = detect_vehicle(file_path, debug=True)

        if vehicle_present:
            notify("Vehicle exited through front gate.")
            return JSONResponse(content={
                "status": "alert_sent",
                "details": "Vehicle detected in clip"
            }, status_code=200)
        else:
            return JSONResponse(content={
                "status": "no_vehicle_detected",
                "details": "No vehicle objects found"
            }, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)