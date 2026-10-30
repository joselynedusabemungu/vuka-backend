from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from vuka.repositories.onboarding import OnboardingRepository


def create_onboarding(db: Session, user_id: int, onboarding):
    repo = OnboardingRepository(db)
    existing = repo.get_by_user(user_id)

    data = onboarding.model_dump(exclude={"user_id"})
    data["user_id"] = user_id

    if existing:
        return repo.update(existing.onboarding_id, data)

    record = repo.create(data)
    db.commit()
    db.refresh(record)
    return record


def get_onboarding(db: Session, onboarding_id: int):
    record = OnboardingRepository(db).get_by_id(onboarding_id)

    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Onboarding assessment not found",
        )

    return record


def get_my_onboarding(db: Session, user_id: int):
    record = OnboardingRepository(db).get_by_user(user_id)

    if not record:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Onboarding assessment not found",
        )

    return record


def update_onboarding(db: Session, onboarding_id: int, onboarding):
    repo = OnboardingRepository(db)

    if not repo.get_by_id(onboarding_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Onboarding assessment not found",
        )

    record = repo.update(
        onboarding_id,
        onboarding.model_dump(exclude_unset=True),
    )

    db.commit()
    db.refresh(record)

    return record


def get_user_onboarding(db: Session, onboarding_id: int, current_user):
    record = get_onboarding(db, onboarding_id)

    if (
        current_user.user_type != "admin"
        and record.user_id != current_user.user_id
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Cannot access another user's onboarding",
        )

    return record


def update_user_onboarding(
    db: Session,
    onboarding_id: int,
    current_user,
    payload,
):
    record = get_onboarding(db, onboarding_id)

    if (
        current_user.user_type != "admin"
        and record.user_id != current_user.user_id
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Cannot modify another user's onboarding",
        )

    return update_onboarding(db, onboarding_id, payload)


def list_all_onboardings(db: Session):
    return OnboardingRepository(db).list_all()
