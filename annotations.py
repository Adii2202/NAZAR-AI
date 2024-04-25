from fastapi import APIRouter
from fastapi import UploadFile, Form
from src.config import AWS_KEY, SECRET_KEY_AWS, S3_BUCKET_NAME
import boto3
import random
import cv2
import numpy as np
import io
import json
import pprint
s3 = boto3.resource(
    service_name='s3',
    aws_access_key_id=f"{AWS_KEY}",
    aws_secret_access_key=f"{SECRET_KEY_AWS}"
)
bucket = s3.Bucket(S3_BUCKET_NAME)

router = APIRouter(
    prefix="/anotations",
    tags=["Anotations"],
    responses={404: {"description": "Not found"}},
)


def getNumberOfObjectsInBucket(prefix):
    files_in_s3 = [f.key.split(prefix)[1] for f in bucket.objects.filter(Prefix=prefix).all()]
    print("Files:",len(files_in_s3))
    return len(files_in_s3)


# function that generates random id of length 8
def generateID():
    id = ""
    for i in range(8):
        if random.random() < 0.5:
            id += chr(random.randint(65,90))
        else:
            id += str(random.randint(0,9))
    return id

@router.post("/create_anotation")
async def create_incident_by_user(image: UploadFile, json_data: str = Form(...)):
    try:
        filename = image.filename.replace(" ","")
        img_extension = filename.split(".")[1]
            
        if img_extension not in ["png", "jpg","jpeg"]:
            return {"ERROR":"INVALID IMAGE FORMAT"}
        byte_im = await image.read()
        data = json.loads(json_data)
        # pprint.pprint(data)
        name =  str(filename.split(".")[0] + generateID())
        for i in range(len(data['annotations'])):

            if 'selectedOptions' not in data['annotations'][i]:
                continue
            selected_options = [option['value'] for option in data['annotations'][i]['selectedOptions']]
            
            yaml = """
            train: ../train/images
            val: ../valid/images
            test: ../test/images

            nc: 1

            names: ['0']
            """
        
            for option in selected_options:
                ### Get the number of files in option/train
                ### Get the number of files in option/valid
                ### Get the number of files in option/test
                ntrain = getNumberOfObjectsInBucket(f"{option}/train/images/")
                nvalid = getNumberOfObjectsInBucket(f"{option}/valid/images/")
                ntest = getNumberOfObjectsInBucket(f"{option}/test/images/")
                total = ntrain + nvalid + ntest

                byte_im_io = io.BytesIO(byte_im)
                w = float(data['annotations'][i]['width'])
                h = float(data['annotations'][i]['height'])
                x = float(data['annotations'][i]['x']) + w/2
                y = float(data['annotations'][i]['y']) + h/2
                label = f"0 {x} {y} {w} {h}\n"
                if ntrain == 0:
                    bucket.upload_fileobj(byte_im_io, f"{option}/train/images/{name}.jpg")
                    s3.Object(S3_BUCKET_NAME, f"{option}/train/labels/{name}.txt").put(Body=label)
                    s3.Object(S3_BUCKET_NAME, f"{option}/data.yaml").put(Body=yaml)
                elif (ntrain)/total*100 < 60:
                    bucket.upload_fileobj(byte_im_io, f"{option}/train/images/{name}.jpg")
                    s3.Object(S3_BUCKET_NAME, f"{option}/train/labels/{name}.txt").put(Body=label)
                elif (nvalid)/total*100 < 20:
                    bucket.upload_fileobj(byte_im_io, f"{option}/valid/images/{name}.jpg")
                    s3.Object(S3_BUCKET_NAME, f"{option}/valid/labels/{name}.txt").put(Body=label)
                else:
                    bucket.upload_fileobj(byte_im_io, f"{option}/test/images/{name}.jpg")
                    s3.Object(S3_BUCKET_NAME, f"{option}/test/labels/{name}.txt").put(Body=label)


        # pprint.pprint(data)
        # uname = str(filename.split(".")[0] + generateID() + ".jpg")
        # bucket.upload_fileobj(byte_im_io, uname)
        # url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{uname}"
    
        # return {"url":url}
        return {"SUCCESS":"IMAGE UPLOADED"}
    except Exception as e:
        print(e)
        return {"ERROR":"SOME ERROR OCCURRED"}

