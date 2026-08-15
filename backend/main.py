from fastapi import FastAPI

from app.api.chat import router as chat_router


app = FastAPI(
    title="Engineering Intelligence Agent",
    description="AI-powered engineering assistant",
    version="0.1.0",
)


app.include_router(
    chat_router,
    prefix="/api/v1",
    tags=["Agent"],
)


@app.get("/")
def root():
    return {
        "name": "Engineering Intelligence Agent",
        "version": "0.1.0",
        "status": "online",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }