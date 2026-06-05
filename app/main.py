import logging
import time

import logfire
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import iterate_in_threadpool

from app.core.config import config
from app.exceptions.exceptions import BusinessException

_logfire_on = config.LOGFIRE_ENABLED and bool(config.LOGFIRE_TOKEN)

if config.LOGFIRE_ENABLED and not config.LOGFIRE_TOKEN:
    logging.getLogger(__name__).warning("LOGFIRE_ENABLED=true but LOGFIRE_TOKEN is missing")

if _logfire_on:
    logfire.configure(token=config.LOGFIRE_TOKEN, inspect_arguments=False)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)

from app.api.v1.messages import router as messages_router
from app.core.logging import setup_logging

logger = setup_logging(config.APP_NAME)

app = FastAPI(docs_url="/api/v1/docs")
app.include_router(messages_router, prefix="/api/v1")

if _logfire_on:
    logfire.instrument_fastapi(app)


@app.get("/")
def main():
    return {
        "message": "Welcome to AI Message Router API. For documentation visit /api/v1/docs for more information"
    }


@app.middleware("http")
async def handle_logging(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    url = request.url.path

    logger.info("Request: %s %s from %s", method, url, client_ip)
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    status_code = response.status_code
    res_body = [section async for section in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(res_body))

    logger.info("Response: %s %s returned %s to %s", method, url, status_code, client_ip)
    if res_body and config.DEBUG:
        res_body = res_body[0].decode()
        logger.info("Response body: \n%s", res_body)
    return response


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
