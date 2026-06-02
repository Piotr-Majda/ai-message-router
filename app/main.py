import time
from fastapi import FastAPI, Request
from starlette.concurrency import iterate_in_threadpool
from app.api.v1.ai_agent import router as ai_agent
from app.core.config import config
from app.core.logging import setup_logging

logger = setup_logging(config.app_name)

app = FastAPI(docs_url="/api/v1/docs")

app.include_router(ai_agent, prefix="/api/v1")

@app.get("/")
def main():
    return {"message": "Welcome to AI Message Router API. For documentation visit /api/v1/docs for more information"}


@app.middleware('http')
async def handle_logging(request: Request, call_next):
    client_ip = request.client.host if request.client else 'unknown'
    method = request.method
    url = request.url.path

    logger.info(f"Request: {method} {url} from {client_ip}")
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    status_code = response.status_code
    res_body = [section async for section in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(res_body))

    logger.info(f"Response: {method} {url} returned {status_code} to {client_ip}")
    if res_body:
        res_body = res_body[0].decode()
        logger.info(f"Response body: \n{res_body}")
    return response