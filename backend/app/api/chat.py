from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.eia_agent import run_eia


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    response = run_eia(request.message)

    return ChatResponse(response=response)