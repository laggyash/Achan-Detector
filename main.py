from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil, os
from detector import *
app = FastAPI()

state = {"vehicle_out": False, "person_out": False}

@app.post("/upload-clip")
async def upload_clip(file: UploadFile = File(...)):

    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    detected_vehicle = detectVehicle(file_path)
    detected_person = detectPersonOrVehicle(file_path)

    state["vehicle_out"] = detected_vehicle
    state["person_out"] = detected_person

    return {"message": "Detection complete", "state": state}

@app.get("/status")
def get_status():
    return state