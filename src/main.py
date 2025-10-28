from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import wallets_router
from src.config import config
from src.db.session import session_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    await session_manager.init_db(run_migrations=True)
    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[""],
)


prefix = "/api/v1"
app.include_router(wallets_router, prefix=prefix)


if __name__ == "__main__":
    uvicorn.run(
        app="src.main:app",
        host=config.uvicorn.host,
        port=config.uvicorn.port,
        workers=config.uvicorn.workers,
        reload=config.uvicorn.reload,
    )
