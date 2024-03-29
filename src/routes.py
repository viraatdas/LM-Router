from collections import defaultdict
from typing import DefaultDict, List
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pydantic import BaseModel
import os
from datetime import datetime

from fine_tune.fine_tune import tune_model
from workflow_definitions import (
    JobResponse,
    JobStatus,
    JobType,
    TrainingPayload,
    UserLoginSchema,
    UserRegistrationSchema,
)

from db.dynamodb_utils import (
    get_jobs_for_api_key,
    update_job_response,
    verify_api_key,
    add_job_response,
)

router = APIRouter()


@router.post("/login")
def login(user_credentials: UserLoginSchema):
    # Login logic here
    return {"token": "user_token"}


@router.post("/register")
def register(user_data: UserRegistrationSchema):
    # Registration logic here
    return {"message": "User registered successfully"}


@router.post("/fine-tune", response_model=JobResponse)
async def fine_tune_model(
    background_tasks: BackgroundTasks,
    dataset: UploadFile = File(...),
    api_key: str = Form(...),
    base_model: str = Form(...),
    job_id: str = Form(...),
):
    # Validate api_key using DynamoDB
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Validate the payload structure
    # TODO: Implement this

    job_details = JobResponse(
        job_id=job_id,
        type=JobType.FINE_TUNE,
        status=JobStatus.STARTING,
        time_started=datetime.now(),
    )

    add_job_response(api_key, job_details)

    output_dir = os.getenv("FINE_TUNED_MODELS_DIR", "./fine_tuned_models")
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate a filename using the caller_id
    job_filename = f"{job_id}-{JobType.FINE_TUNE}.json"
    dataset_file_path = os.path.join(output_dir, job_filename)

    # Save the uploaded dataset file
    with open(dataset_file_path, "wb") as f:
        contents = await dataset.read()
        f.write(contents)

    # Start the model training in the background
    background_tasks.add_task(
        tune_model,
        job_details=job_details,
        output_dir=output_dir,
        dataset_path=dataset_file_path,
        base_model=base_model,
        api_key=api_key,
    )

    job_details.status = JobStatus.RUNNING
    update_job_response(api_key, job_details)

    return job_details


@router.get("/job-status/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str, api_key: str):
    # Validate api_key
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Get job details based on api_key
    jobs = get_jobs_for_api_key(api_key)
    job_details = next((job for job in jobs if job.id == job_id), None)

    if not job_details:
        raise HTTPException(status_code=404, detail="Job not found")

    return job_details


@router.get("/list-all-jobs")
def list_all_jobs(api_key: str):
    # Validate api_key
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return get_jobs_for_api_key(api_key)


# Generate playground
# @router.post("/test-playground")
# def get_test_playground(payload: FineTunePayload, api_key: str):
#     generate_gradio_playground(base_model="yahma/llama-7b-hf")


# Training model
@router.post("/train")
def train_model(payload: TrainingPayload):
    raise NotImplemented("method not implemented")


# @router.get("/job_status/{job_id}")
# def get_job_status(job_id: str):
#     # Retrieve the job status from the in-memory data structure
#     return {"job_id": job_id, "status": job_statuses.get(job_id, "NOT_FOUND")}

# User registration

# class UserRegistration(BaseModel):
#     email: str

# @router.post('/register')
# def register(user: UserRegistration):
#     # Check if user already exists
#     if user.email in api_keys:
#         raise HTTPException(status_code=400, detail='User already registered. Contact viraat@inferent.io to request another API key.')

#     # Create new API key
#     api_key = generate_api_key()

#     # Store user and API key
#     api_keys[user.email] = api_key

#     return {'api_key': api_key}
