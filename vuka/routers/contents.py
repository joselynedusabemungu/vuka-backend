from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from vuka.dependency import get_current_user, require_admin
from vuka.models.registration import Registration
from vuka.schemas.contents import ContentResponse
from vuka.schemas.content_pathway import RecommendedContentResponse
from vuka.services.contents import ContentService


router = APIRouter(tags=["Contents"])


def get_service(db: Session = Depends(get_db)) -> ContentService:
    return ContentService(db)


@router.post(
    "/serper",
    response_model=list[ContentResponse],
    status_code=status.HTTP_201_CREATED,
)
def fetch_and_save_serper(
    query: str,
    service: ContentService = Depends(get_service),
    current_user: Registration = Depends(require_admin),
):
    return service.fetch_and_save_from_serper(query)


@router.post(
    "/youtube",
    response_model=list[ContentResponse],
    status_code=status.HTTP_201_CREATED,
)
def fetch_and_save_youtube(
    query: str,
    service: ContentService = Depends(get_service),
    current_user: Registration = Depends(require_admin),
):
    return service.fetch_and_save_from_youtube(query)


@router.get(
    "/recommended",
    response_model=list[RecommendedContentResponse],
)
async def get_recommended_content(
    limit: int = 20,
    service: ContentService = Depends(get_service),
    current_user: Registration = Depends(get_current_user),
):
    return await service.get_recommended_for_user(
        current_user.user_id,
        limit,
    )


@router.get(
    "",
    response_model=list[ContentResponse],
)
def list_contents(
    skip: int = 0,
    limit: int = 50,
    service: ContentService = Depends(get_service),
    current_user: Registration = Depends(get_current_user),
):
    return service.get_all(skip, limit)


@router.get(
    "/{content_id}",
    response_model=ContentResponse,
)
def get_content(
    content_id: int,
    service: ContentService = Depends(get_service),
    current_user: Registration = Depends(get_current_user),
):
    return service.get_by_id(content_id)
