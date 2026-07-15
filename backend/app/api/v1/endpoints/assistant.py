from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.assistant import AssistantQueryRequest, AssistantResponse
from app.domains.assistant.agent import AgenticAIAssistant
from app.core.config import settings
from typing import Optional

router = APIRouter()

@router.post("/query", response_model=AssistantResponse)
def ask_assistant(
    request: AssistantQueryRequest,
    tenant_id: Optional[str] = Header(None, alias=settings.TENANT_HEADER),
    db: Session = Depends(get_db)
):
    """
    Agentic AI chatbot tool routing queries about order states, machine status, schedules, and scenario runs.
    """
    t_id = tenant_id or settings.DEFAULT_TENANT_ID
    res = AgenticAIAssistant.answer_query(db, request.query, t_id)
    return res
