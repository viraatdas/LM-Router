from fastapi import FastAPI
from routes import router
from db.dynamodb_utils import add_api_key, initialize_dynamodb_tables

app = FastAPI()

# Initialize DynamoDB tables
initialize_dynamodb_tables()
add_api_key("test-api-key", "test@test.com")


@app.get("/")
def read_root():
    return {"Welcome to the:" "future of deep learning"}


app.include_router(router)
