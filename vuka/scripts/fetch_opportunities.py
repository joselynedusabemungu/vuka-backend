from __future__ import annotations
import argparse
from database import SessionLocal
from vuka.models.enums import SubjectFieldEnum
from vuka.services.opportunity_recommendation import OpportunityRecommendationService


def run(subject: str | None, query: str | None, num_results: int) -> None:
    db = SessionLocal()
    try:
        service = OpportunityRecommendationService(db)
        if subject:
            created = service.fetch_and_store_by_subject(SubjectFieldEnum(subject), query, num_results)
        else:
            created = []
            for field in SubjectFieldEnum:
                created.extend(service.fetch_and_store_by_subject(field, None, num_results))
        print(f"Stored {len(created)} new opportunities.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch opportunities from Serper into the pool table.")
    parser.add_argument("--subject", choices=[field.value for field in SubjectFieldEnum], default=None)
    parser.add_argument("--query", default=None)
    parser.add_argument("--num-results", type=int, default=10)
    args = parser.parse_args()
    run(args.subject, args.query, args.num_results)
