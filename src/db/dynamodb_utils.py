import boto3
from workflow_definitions import JobResponse
from boto3.dynamodb.conditions import Key  # Importing Key
from typing import List

dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
API_KEYS_TABLE = dynamodb.Table("APIKeys")
JOB_RESPONSES_TABLE = dynamodb.Table("APIKeyToJobResponses")


def create_table_if_not_exists(
    table_name, attribute_definitions, key_schema, provisioned_throughput
):
    existing_tables = dynamodb.meta.client.list_tables()["TableNames"]

    if table_name in existing_tables:
        print(f"Table {table_name} already exists.")
        return

    table = dynamodb.create_table(
        TableName=table_name,
        AttributeDefinitions=attribute_definitions,
        KeySchema=key_schema,
        ProvisionedThroughput=provisioned_throughput,
    )

    table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
    print(f"Table {table_name} created successfully.")


def initialize_dynamodb_tables():
    create_table_if_not_exists(
        "APIKeys",
        [{"AttributeName": "api_key", "AttributeType": "S"}],
        [{"AttributeName": "api_key", "KeyType": "HASH"}],
        {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )

    create_table_if_not_exists(
        "APIKeyToJobResponses",
        [
            {"AttributeName": "api_key", "AttributeType": "S"},
            {"AttributeName": "job_id", "AttributeType": "S"},
        ],
        [
            {"AttributeName": "api_key", "KeyType": "HASH"},
            {"AttributeName": "job_id", "KeyType": "RANGE"},
        ],
        {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )


def add_api_key(api_key: str, email: str):
    API_KEYS_TABLE.put_item(Item={"api_key": api_key, "email": email})
    print(f"API key for {email} added successfully.")


def verify_api_key(api_key: str) -> bool:
    response = API_KEYS_TABLE.get_item(Key={"api_key": api_key})
    return "Item" in response


def add_job_for_api_key(api_key: str, job_response: JobResponse):
    item = job_response.dump()
    item["api_key"] = api_key
    JOB_RESPONSES_TABLE.put_item(Item=item)


def get_jobs_for_api_key(api_key: str) -> List[JobResponse]:
    response = JOB_RESPONSES_TABLE.query(
        KeyConditionExpression=Key("api_key").eq(api_key)
    )
    return [JobResponse(**item) for item in response.get("Items", [])]


def add_job_response(api_key: str, job_response: JobResponse):
    """
    Add a new job response for a given API key to the DynamoDB table.

    :param api_key: API key associated with the job.
    :param job_response: Details of the job to be added.
    :return: None
    """
    item = job_response.dump()
    item["api_key"] = api_key
    JOB_RESPONSES_TABLE.put_item(Item=item)


def update_job_response(api_key: str, job_details: JobResponse):
    response = JOB_RESPONSES_TABLE.query(
        KeyConditionExpression=Key("api_key").eq(api_key)
    )
    if "Items" in response:
        # Find the job by job_id and update its details
        for item in response["Items"]:
            if item["job_id"] == job_details.job_id:
                # Use the dump method to serialize the JobResponse instance
                updated_item = job_details.dump()
                updated_item["api_key"] = api_key
                JOB_RESPONSES_TABLE.put_item(Item=updated_item)
                break
