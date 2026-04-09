from fastapi import APIRouter, Depends

from models.api import AskRequest, AskResponse
from services.assistant_service import AssistantService, get_assistant_service


router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask(
    payload: AskRequest,
    service: AssistantService = Depends(get_assistant_service),
) -> AskResponse:
    return await service.ask(payload)

