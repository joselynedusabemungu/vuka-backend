from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from vuka.dependency import get_current_user, require_admin
from vuka.models.enums import SubjectFieldEnum
from vuka.models.registration import Registration
from vuka.schemas.opportunity_recommendation import (
    OpportunityRecommendationRead,
    OpportunityRecommendationUpdate,
    OpportunitySubjectFetchRequest,
    UserOpportunityResponse,
)
from vuka.services.opportunity_recommendation import OpportunityRecommendationService

router = APIRouter(
    prefix="/opportunity-recommendations", tags=["Opportunity Recommendations"]
)


@router.get("/me", response_model=UserOpportunityResponse)
def my_opportunities(
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return OpportunityRecommendationService(db).get_my_opportunities(
        current_user.user_id
    )


@router.post(
    "/me/refresh",
    response_model=UserOpportunityResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_my_opportunities(
    db: Session = Depends(get_db),
    current_user: Registration = Depends(get_current_user),
):
    return OpportunityRecommendationService(db).refresh_for_user(current_user.user_id)


@router.get("/", response_model=list[OpportunityRecommendationRead])
def list_opportunities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(require_admin),
):
    return OpportunityRecommendationService(db).list_opportunities(skip, limit)


@router.get(
    "/subject/{subject_field}", response_model=list[OpportunityRecommendationRead]
)
def list_opportunities_by_subject(
    subject_field: SubjectFieldEnum,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(require_admin),
):
    return OpportunityRecommendationService(db).list_opportunities_by_subject(
        subject_field, skip, limit
    )


@router.get("/{opportunity_id}", response_model=OpportunityRecommendationRead)
def get_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(require_admin),
):
    return OpportunityRecommendationService(db).get_opportunity(opportunity_id)


@router.patch("/{opportunity_id}", response_model=OpportunityRecommendationRead)
def update_opportunity(
    opportunity_id: int,
    data: OpportunityRecommendationUpdate,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(require_admin),
):
    return OpportunityRecommendationService(db).patch_opportunity(opportunity_id, data)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: Registration = Depends(require_admin),
):
    OpportunityRecommendationService(db).delete_opportunity(opportunity_id)
    return None

    service = OpportunityRecommendationService(db)
    return service.patch_opportunity(
        opportunity_id, OpportunityRecommendationUpdate(user_id=None)
    )


@router.post(
    "/fetch-by-subject",
    response_model=list[OpportunityRecommendationRead],
    status_code=status.HTTP_201_CREATED,
    summary="Fetch opportunities for one subject field via Serper",
    description=(
        "Searches Serper for the given (or default) query for a subject "
        "field and stores each new result unassigned, ready for AI matching."
    ),
)
def fetch_opportunities_by_subject(
    payload: OpportunitySubjectFetchRequest, db: Session = Depends(get_db)
):
    service = OpportunityRecommendationService(db)
    return service.fetch_and_store_by_subject(
        payload.subject_field, payload.query, payload.num_results
    )


@router.post(
    "/fetch-all-subjects",
    response_model=list[OpportunityRecommendationRead],
    status_code=status.HTTP_201_CREATED,
    summary="Fetch opportunities across every subject field via Serper",
)
def fetch_opportunities_all_subjects(
    num_results: int = 10, db: Session = Depends(get_db)
):

    return OpportunityRecommendationService(db).fetch_and_store_all_subjects(
        num_results
    )
