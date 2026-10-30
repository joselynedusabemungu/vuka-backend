from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Registration(Base):
    __tablename__ = "registrations"

    user_id = Column(Integer, primary_key=True, autoincrement=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    pass_hash = Column(String, nullable=False)
    preferred_language = Column(String, nullable=True)
    country = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, nullable=False, server_default="true")
    user_type = Column(String, nullable=False, server_default="user")
    failed_login_attempts = Column(Integer, nullable=False, server_default="0")
    locked_until = Column(DateTime(timezone=True), nullable=True)
    mfa_enabled = Column(Boolean, nullable=False, server_default="false")
    mfa_secret_encrypted = Column(String(512), nullable=True)
    mfa_challenge_jti = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    opportunity_recommendations = relationship(
        "OpportunityRecommendation", back_populates="user", cascade="all, delete-orphan"
    )
    user_progress = relationship(
        "UserProgress", back_populates="registration", cascade="all, delete-orphan"
    )
    verified_assessments = relationship(
        "VerifiedAssessment", back_populates="registration", cascade="all, delete-orphan"
    )
    onboarding = relationship(
        "Onboarding", back_populates="registration", uselist=False, cascade="all, delete-orphan"
    )
