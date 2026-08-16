from fastapi import APIRouter
from pydantic import BaseModel

from app.graph.eia_graph import eia_graph


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = eia_graph.invoke(
        {
            "user_message": request.message,
            "response": "",
        }
    )

    return ChatResponse(
        response=result["response"]
    )