from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_service import generate_code


router = APIRouter(
    prefix="/api/coding",
    tags=["Coding Agent"]
)


class CodingRequest(BaseModel):
    prompt: str


@router.post("/generate")
def generate(request: CodingRequest):
    try:
        result = generate_code(request.prompt)

        return {
            "status": "success",
            "prompt": request.prompt,
            "response": result,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )