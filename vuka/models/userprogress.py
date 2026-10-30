from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "assessment_id", name="uq_user_progress_user_assessment"),
    )

    progress_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("registrations.user_id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("verified_assessments.assessment_id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    streak_count = Column(Integer, nullable=False, default=0)
    performance_tier = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    registration = relationship("Registration", back_populates="user_progress")
    assessment = relationship("VerifiedAssessment", back_populates="user_progress")
