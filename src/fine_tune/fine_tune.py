import json
from db.dynamodb_utils import update_job_response

from package_external.LLM_Adapters.finetune import train
from workflow_definitions import JobResponse, JobStatus
from datetime import datetime


def write_dataset_to_file(dataset, file_path):
    with open(file_path, "w") as file:
        json.dump(dataset, file)


def tune_model(
    job_details: JobResponse,
    base_model: str,
    dataset_path: str,
    output_dir: str,
    api_key: str,
):
    try:
        train(
            base_model=base_model,
            output_dir=output_dir,
            data_path=dataset_path,
            use_gradient_checkpointing=True,
            batch_size=8,
            micro_batch_size=2,
            num_epochs=1,
            val_set_size=3,
        )
        job_details.status = JobStatus.COMPLETED
    except Exception as e:
        job_details.status = JobStatus.ERROR
        job_details.error_msg = str(e)
    finally:
        job_details.time_ended = datetime.now()
        update_job_response(api_key, job_details)
