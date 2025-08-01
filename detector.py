import os
import json
import cv2
import shutil
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from ultralytics import YOLO 
from dotenv import load_dotenv
import numpy as np

load_dotenv()

model = YOLO("yolov8n.pt")
vehicle_classes = ["car", "motorcycle", "truck", "bus"]
person_class = "person"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

exit_box = "exit_point.json"
with open(exit_box) as f:
        data = json.load(f)
        exit_point = tuple(data["exit_point"])

app = FastAPI(title="Detection")

def atExitPoint(box, threshold=0.5):
    x1, y1, x2, y2 = map(int, box)
    gx1, gy1, gx2, gy2 = exit_point

    ix1 = max(x1, gx1)
    iy1 = max(y1, gy1)
    ix2 = min(x2, gx2)
    iy2 = min(y2, gy2)

    inter_area = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    box_area = (x2 - x1) * (y2 - y1)

    return (inter_area / box_area) > threshold

def detectVehicle(video_path: str, debug: bool = True) -> bool:

    cap = cv2.VideoCapture(video_path)
    found_vehicle = False
    frame_count = 0
    if os.path.exists("debug_frames"):
      shutil.rmtree("debug_frames")
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

                if cls_name in ["car", "motorcycle", "truck", "bus"]:
                    if atExitPoint(box):
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

def detectPersonOrVehicle(video_path: str, debug: bool = True):
    found_person_or_vehicle = False
    frame_count = 0

    if os.path.exists("debug_frames"):
      shutil.rmtree("debug_frames")

    if debug:
        os.makedirs("debug_frames", exist_ok=True)

    cap = cv2.VideoCapture(video_path)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 5 != 0:
            continue

        results = model(frame, verbose=False)

        for r in results:
            if r.boxes is None:
                continue

            for box, cls_id in zip(r.boxes.xyxy, r.boxes.cls):
                cls_name = model.names[int(cls_id)]

                if not atExitPoint(box):
                    if debug:
                        annotated = r.plot()
                        cv2.rectangle(annotated, (exit_point[0], exit_point[1]),
                                      (exit_point[2], exit_point[3]), (0, 0, 255), 2)
                        cv2.imwrite(f"debug_frames/frame_{frame_count}_out.jpg", annotated)
                    continue

                if cls_name in vehicle_classes:
                    found_person_or_vehicle = True

                if cls_name == person_class:
                    found_person_or_vehicle = True

                if debug and found_person_or_vehicle:
                    annotated = r.plot()
                    cv2.rectangle(annotated, (exit_point[0], exit_point[1]),
                                  (exit_point[2], exit_point[3]), (0, 255, 255), 2)
                    cv2.imwrite(f"debug_frames/frame_{frame_count}.jpg", annotated)

        if found_person_or_vehicle:
            break

    cap.release()
    print(f"[DEBUG] Frames processed: {frame_count}, Person/Vehicle detected: {found_person_or_vehicle}")
    return found_person_or_vehicle