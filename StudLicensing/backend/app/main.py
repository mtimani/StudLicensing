from fastapi import FastAPI
from tests.test_models import test_db



app = FastAPI()
test_db()


@app.get("/")
def read_root():
    return {"message": "Hello world"}