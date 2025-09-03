from fastapi import APIRouter, Depends

from auth import verify_token
from schemas.semantic_mapping import SemanticMappingResponse
from services import semantic_mapping_service

router = APIRouter(prefix="/mappings")


@router.get("/{db_connection_id}", response_model=SemanticMappingResponse)
async def get_mapping(db_connection_id: str, token_data: dict = Depends(verify_token)) -> SemanticMappingResponse:
    mappings = await semantic_mapping_service.get_mapping(token_data["user_id"], db_connection_id)
    return SemanticMappingResponse(mappings=mappings)
