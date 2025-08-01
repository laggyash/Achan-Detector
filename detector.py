import os
import shutil
import json
import cv2
from fastapi 
import FastAPI, File, UploadFile
from fastapi.responses 
import JSONResponse
from ultralytics 
import YOLO
import requests
from dotenv import load_dotenv

load_dotenv()

model = YOLO("yolov8n.pt")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

exit_box = "exit_point.json"
with open(exit_box) as f:
        data = json.load(f)
        exit_point = tuple(data["exit_point"])
app = FastAPI(title="Local Vehicle Detection")

def notify(message: str):
    print(message)

def is_in_gate_zone(box):
    if exit_point is None:
        return True

    x1, y1, x2, y2 = map(int, box) 
    gx1, gy1, gx2, gy2 = exit_point

    return not (x2 < gx1 or x1 > gx2 or y2 < gy1 or y1 > gy2)

def detect_vehicle(video_path: str, debug: bool = True) -> bool:

    #shutil.rmtree("debug_frames")
    cap = cv2.VideoCapture(video_path)
    found_vehicle = False
    frame_count = 0

    os.makedirs("debug_frames", exist_ok=True) if debug else None
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 5 != 0:  # skip frames for performance
            continue

        results = model(frame, verbose=False)

        for r in results:
            for box, cls_id in zip(r.boxes.xyxy, r.boxes.cls):
                cls_name = model.names[int(cls_id)]

                if cls_name in ["car", "motorcycle", "truck", "bus"]:
                    if is_in_gate_zone(box):
                        found_vehicle = True

                        if debug:
                            annotated = r.plot()
                            cv2.rectangle(
                                annotated,
                                (exit_point[0], exit_point[1]),
                                (exit_point[2], exit_point[3]),
                                (0, 255, 255),
                                2
                            )
                            cv2.imwrite(f"debug_frames/frame_{frame_count}.jpg", annotated)
                    else:
                        if debug:
                            annotated = r.plot()
                            cv2.rectangle(
                                annotated,
                                (exit_point[0], exit_point[1]),
                                (exit_point[2], exit_point[3]),
                                (0, 0, 255),
                                2
                            )
                            cv2.imwrite(f"debug_frames/frame_{frame_count}_out.jpg", annotated)

        if found_vehicle:
            break

    cap.release()
    print(f"[DEBUG] Frames processed: {frame_count}, Vehicle Detected: {found_vehicle}")
    return found_vehicle


@app.post("/upload-clip")
async def upload_clip(file: UploadFile = File(...)):
    if os.path.exists("debug_frames"):
      shutil.rmtree("debug_frames")
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename) # type: ignore
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