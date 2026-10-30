from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class VerifiedAssessment(Base):
    __tablename__ = "verified_assessments"

    assessment_id = Column(Integer, primary_key=True, index=True)
    generated_assessment_id = Column(
        Integer, ForeignKey("generated_assessment.assessment_id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    user_id = Column(Integer, ForeignKey("registrations.user_id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    score = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, server_default="in_progress", index=True)
    answers = Column(JSONB, nullable=False, server_default="{}")
    current_step = Column(Integer, nullable=False, server_default="0")
    performance_tier = Column(String(20), nullable=True)
    streak_awarded = Column(Integer, nullable=False, server_default="0")
    assessment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    generated_assessment = relationship("GeneratedAssessment", back_populates="verified_assessments")
    registration = relationship("Registration", back_populates="verified_assessments")
    user_progress = relationship("UserProgress", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
