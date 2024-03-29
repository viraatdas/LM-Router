"""
Job Status

What stage of the workflow is the job in

"""


from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from fastapi import UploadFile


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserRegistrationSchema(BaseModel):
    email: EmailStr
    password: str


class JobStatus(Enum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    ERROR = "ERROR"


"""
Job Type

The type of job 
"""


class JobType(Enum):
    FINE_TUNE = "FINE_TUNE"
    DEPLOY_MODEL_AS_ENDPOINT = "DEPLOY_MODEL_AS_ENDPOINT"
    TRAIN = "TRAIN"


# Fine tuning
class FineTunePayload(BaseModel):
    caller_id: str
    base_model: str
    api_key: str
    dataset_bytes: UploadFile
    email: str = Field("")


class JobResponse(BaseModel):
    job_id: str
    type: JobType
    error_msg: str = "No error"
    status: JobStatus
    time_started: datetime
    time_ended: datetime = None

    def dump(self):
        data = self.model_dump()
        # Convert enums to strings
        data["type"] = data["type"].value
        data["status"] = data["status"].value
        # Convert datetimes to ISO format strings
        data["time_started"] = data["time_started"].isoformat()
        if data["time_ended"]:
            data["time_ended"] = data["time_ended"].isoformat()

        return data


class TrainingPayload(BaseModel):
    dataloader: bytes
    model: bytes
