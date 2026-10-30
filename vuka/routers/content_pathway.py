from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from vuka.dependency import get_current_user
from vuka.models.registration import Registration
from vuka.schemas.content_pathway import (
    ContentPathwayCreate,
    ContentPathwayResponse,
    ContentPathwayUpdate,
)
from vuka.services.content_pathway import ContentPathwayService

router = APIRouter(
    prefix="/content_pathway",
    tags=["Content Pathways"],
)


def get_pathway_service(db: Session = Depends(get_db)):
    return ContentPathwayService(db)


@router.get("/me", response_model=list[ContentPathwayResponse])
async def get_my_pathway(
    skip: int = 0,
    limit: int = 50,
    current_user: Registration = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from vuka.services.contents import ContentService

    content_service = ContentService(db)
    return await content_service.get_recommended_for_user(
        user_id=current_user.user_id, limit=limit
    )


@router.post(
    "", response_model=ContentPathwayResponse, status_code=status.HTTP_201_CREATED
)
def create_pathway(
    pathway_in: ContentPathwayCreate,
    service: ContentPathwayService = Depends(get_pathway_service),
    current_user: Registration = Depends(get_current_user),
):
    return service.create_for_user(
        current_user.user_id, pathway_in.model_dump(mode="json")
    )


@router.get("/{content_pathway_id}", response_model=ContentPathwayResponse)
def get_pathway(
    content_pathway_id: int,
    service: ContentPathwayService = Depends(get_pathway_service),
    current_user: Registration = Depends(get_current_user),
):
    return service.get_for_user(current_user.user_id, content_pathway_id)


@router.post("/{content_pathway_id}/watched", response_model=ContentPathwayResponse)
def mark_watched(
    content_pathway_id: int,
    background_tasks: BackgroundTasks,
    service: ContentPathwayService = Depends(get_pathway_service),
    current_user: Registration = Depends(get_current_user),
):
    record = service.mark_watched_for_user(current_user.user_id, content_pathway_id)
    background_tasks.add_task(
        ContentPathwayService.generate_assessment_after_watched,
        record.content_id,
    )
    return record


@router.patch("/{content_pathway_id}", response_model=ContentPathwayResponse)
def update_pathway(
    content_pathway_id: int,
    payload: ContentPathwayUpdate,
    service: ContentPathwayService = Depends(get_pathway_service),
    current_user: Registration = Depends(get_current_user),
):
    return service.update_for_user(current_user.user_id, content_pathway_id, payload)


@router.delete("/{content_pathway_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pathway(
    content_pathway_id: int,
    service: ContentPathwayService = Depends(get_pathway_service),
    current_user: Registration = Depends(get_current_user),
):
    service.delete_for_user(current_user.user_id, content_pathway_id)
