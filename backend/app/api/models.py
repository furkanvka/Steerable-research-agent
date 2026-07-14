from fastapi import APIRouter
from app.ollama.client import get_models

router = APIRouter()


@router.get("/models")
async def list_models():
    models = await get_models()
    return {"models": models}
