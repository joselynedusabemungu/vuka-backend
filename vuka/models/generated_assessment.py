from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class GeneratedAssessment(Base):
    __tablename__ = "generated_assessment"

    assessment_id = Column(Integer, primary_key=True, index=True)
    content_id = Column(
        Integer,
        ForeignKey("content.content_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    category = Column(String(50), nullable=False)
    questions = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=False, default="gemini-3.5-flash")
    generated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    content = relationship("Content", back_populates="generated_assessment")
    verified_assessments = relationship(
        "VerifiedAssessment", back_populates="generated_assessment"
    )
