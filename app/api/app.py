from uuid import uuid4
from app.config.state import ForgeOpsState,QueryRequest
from fastapi import FastAPI 
import uvicorn 

application = FastAPI()

@application.get("/")
def health_check():
    return {"Hello": "World"}


@application.post("/query}")
async def query(request: QueryRequest):
    thread_id = request.thread_id or str(uuid4())

    state=ForgeOpsState(
        user_query=request.user_query,
        thread_id=thread_id
    )
    return {
        "thread_id": thread_id,
        "response": "None"
    }



def main():
    uvicorn.run(application,port=8000,host="0.0.0.0")


main()