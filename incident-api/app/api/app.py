from __future__ import annotations

import asyncio
import contextlib
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import router
from ..core.runtime import get_runtime


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer_task = asyncio.create_task(get_runtime().result_consumer.run_forever())
    try:
        yield
    finally:
        consumer_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await consumer_task


def create_app() -> FastAPI:
    app = FastAPI(title="SevLens Incident API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("SEVLENS_CORS_ORIGINS", "http://localhost:5173").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(KeyError)
    async def key_error_handler(_: Request, exc: KeyError):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": f"Unknown scenario: {exc.args[0]}"})

    app.include_router(router)
    return app


app = create_app()
