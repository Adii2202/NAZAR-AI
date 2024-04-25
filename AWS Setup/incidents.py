from fastapi import APIRouter
from fastapi import UploadFile, Form
from src.models.incidents_model import Incidents
from src.models.notifications_model import Notifications
from src.database.notifications_db import create_notification
from src.database.incident_db import (create_incident, fetch_all_incidents, fetch_incidents_by_id, fetch_incidents_by_station, delete_incident_by_id, update_incident_station_name, update_incident_status, fetch_incidents_by_userid)
from src.config import AWS_KEY, SECRET_KEY_AWS, S3_BUCKET_NAME
import boto3
import random
from ultralytics import YOLO
import cv2
import numpy as np
import io
from src.utility import get_lat_long, cctv_json, get_lat_long_by_cctv

s3 = boto3.resource(
    service_name='s3',
    aws_access_key_id=f"{AWS_KEY}",
    aws_secret_access_key=f"{SECRET_KEY_AWS}"
)
bucket = s3.Bucket(S3_BUCKET_NAME)

model = YOLO("./assets/fire_optimal.pt")

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
    responses={404: {"description": "Not found"}},
)

def findcctvtype(source):
    for feature in cctv_json["features"]:
        if feature["properties"]["id"] == source:
            return feature["properties"]["cctv_type"]
    return "public"

# function that generates random id of length 8
def generateID():
    id = ""
    for i in range(8):
        if random.random() < 0.5:
            id += chr(random.randint(65,90))
        else:
            id += str(random.randint(0,9))
    return id

@router.post("/create_incident")
def new_incident(incident: Incidents):
    try:
        if incident.title == "" or incident.type == "" or incident.station_name == "" or incident.source == "" or incident.image == "" or incident.location == "":
            return {"ERROR": "MISSING PARAMETERS"}

        incident.lat, incident.long = get_lat_long_by_cctv(incident.source)
    
        result = create_incident(incident)
        notification = Notifications(station_name=incident.station_name, title="New Incident: " + incident.title, description=incident.description, type="incident", image=incident.image)
        create_notification(notification)
        notification = Notifications(station_name=incident.station_name, title="New Incident: " + incident.title, description=incident.description, type="staff_incident", image=incident.image)
        create_notification(notification)
        return result
    except Exception as e:
        print(e)
        return {"ERROR":"SOME ERROR OCCURRED"}

@router.post("/user_incident")
async def create_incident_by_user(image: UploadFile, title: str = Form(...), description: str = Form(...), type: str = Form(...), station_name: str = Form(...), location: str = Form(...), source: str = Form(...)):
    try:
        filename = image.filename.replace(" ","")
        img_extension = filename.split(".")[1]
            
        if img_extension not in ["png", "jpg","jpeg"]:
            return {"ERROR":"INVALID IMAGE FORMAT"}

        # Read the image file into a numpy array
        contents = await image.read()
        nparr = np.fromstring(contents, np.uint8)

        # Decode the image using OpenCV
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        results = model.predict(source=img, save_txt=False)
        img_with_boxes = results[0].plot()
        
        # Save the image with boxes to a BytesIO object
        _, im_buf_arr = cv2.imencode(".jpg", img_with_boxes)
        byte_im = im_buf_arr.tobytes()

        # Create a BytesIO object from the byte array
        byte_im_io = io.BytesIO(byte_im)
        lat, long = get_lat_long(location)
        incident = Incidents(title=title, description=description, type=type, station_name=station_name, location=location, source=source, lat=lat, long=long)

        uname = str(filename.split(".")[0] + generateID() + ".jpg")
        bucket.upload_fileobj(byte_im_io, uname)
        url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{uname}"
        incident.image = url

        result = create_incident(incident)
        
        notification = Notifications(station_name=incident.station_name, title="New Report: " + incident.title, description=incident.description, type="report", image=url)
        create_notification(notification)
        notification = Notifications(station_name=incident.station_name, title="New Report: " + incident.title, description=incident.description, type="staff_report", image=url)
        create_notification(notification)
        return result
    except Exception as e:
        print(e)
        return {"ERROR":"SOME ERROR OCCURRED"}

## get all incidents
@router.get("/all_incidents")
def get_all_incidents():
    return fetch_all_incidents()
    
## get incident by dept name and station name
@router.get("/get_incidents_by_station")
def get_incidents_by_station(station_name: str):
    if station_name == "":
        return {"ERROR": "MISSING PARAMETERS"}
    return fetch_incidents_by_station(station_name)

## get incident by id
@router.get("/get_incident_by_id")
def get_incident_by_id(id: str):
    if id == "":
        return {"ERROR": "MISSING PARAMETERS"}
    return fetch_incidents_by_id(id)

@router.delete("/delete_incident")
def delete_incident(id: str):
    if id == "":
        return {"ERROR": "MISSING PARAMETERS"}
    return delete_incident_by_id(id)

@router.put("/update_incident_status")
def update_status(id: str, status: str):
    if id == "" or status == "":
        return {"ERROR": "MISSING PARAMETERS"}
    return update_incident_status(id, status)

@router.get("/get_incidents_by_userid")
def get_incidents_by_userid(id: str):
    if id == "":
        return {"ERROR": "MISSING PARAMETERS"}
    return fetch_incidents_by_userid(id)

@router.get("/update_incident_station_name")
def update_incident_station_name_endp(id: str, station_name: str):
    if id == "" or station_name == "":
        return {"ERROR": "MISSING PARAMETERS"}
    return update_incident_station_name(id, station_name)