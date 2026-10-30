from sqlalchemy.orm import Session

from vuka.models.opportunity_recommendation import (
    OpportunityRecommendation,
)


class OpportunityRecommendationRepository:

    def __init__(self, db: Session):
        self.db = db

    def get(self, opportunity_id: int):
        return (
            self.db.query(OpportunityRecommendation)
            .filter(OpportunityRecommendation.opportunity_id == opportunity_id)
            .first()
        )

    def create(self, data: dict) -> OpportunityRecommendation:
        record = OpportunityRecommendation(**data)
        self.db.add(record)
        self.db.flush()
        return record
    
    def list(self, skip: int = 0, limit: int = 100,):
        return (
            self.db.query(OpportunityRecommendation)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_user(self, user_id: int, progress_id: int | None = None,):

        query = (
            self.db.query(OpportunityRecommendation)
            .filter(OpportunityRecommendation.user_id == user_id)
        )

        if progress_id is not None:
            query = query.filter(OpportunityRecommendation.progress_id== progress_id
            )

        return (
            query
            .order_by(OpportunityRecommendation.match_score.desc().nullslast(), OpportunityRecommendation.opportunity_date.desc(),)
            .all()
        )

    def list_by_subject(self, subject_field, skip: int = 0, limit: int = 100,
    ):

        return (
            self.db.query(OpportunityRecommendation)
            .filter(OpportunityRecommendation.subject_field == subject_field
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_urls_by_subject(self, subject_field):

        rows = (
            self.db.query(OpportunityRecommendation.external_media_url)
            .filter(OpportunityRecommendation.subject_field == subject_field)
            .all()
        )
        return {row[0] for row in rows}

    def list_urls_for_user_progress(self, user_id: int, progress_id: int,):
        rows = (
            self.db.query(OpportunityRecommendation.external_media_url)
            .filter(OpportunityRecommendation.user_id == user_id, OpportunityRecommendation.progress_id == progress_id,)
            .all()
        )
        return {row[0] for row in rows}

    def list_unassigned(self, skip: int = 0, limit: int = 100,
    ):
        return (
            self.db.query(OpportunityRecommendation)
            .filter(
                OpportunityRecommendation.user_id.is_(None)
            )
            .order_by( OpportunityRecommendation.opportunity_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_available_pool(
        self,
        limit: int = 100,
    ):

        return (
            self.db.query(OpportunityRecommendation)
            .filter( OpportunityRecommendation.user_id.is_(None),
                OpportunityRecommendation.progress_id.is_(None),
            )
            .order_by(
                OpportunityRecommendation.opportunity_date.desc()
            )
            .limit(limit)
            .all()
        )

    def update(self, record, data: dict):
        for field, value in data.items():
            setattr(record, field, value)
        self.db.flush()
        return record

    def delete(self, record) -> None:
        self.db.delete(record)
        self.db.flush()