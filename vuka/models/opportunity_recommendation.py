from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base
from .enums import SubjectFieldEnum


class OpportunityRecommendation(Base):
    __tablename__ = "opportunity_recommendation"

    opportunity_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("registrations.user_id", ondelete="CASCADE"), nullable=True, index=True)
    progress_id = Column(Integer, ForeignKey("user_progress.progress_id", ondelete="SET NULL"), nullable=True, index=True)
    subject_field = Column(Enum(SubjectFieldEnum, name="subject_field_enum"), nullable=False, index=True)
    external_media_url = Column(Text, nullable=False)
    source_platform = Column(String(100), nullable=False)
    media_description = Column(Text, nullable=False)
    opportunity_date = Column(DateTime, nullable=False)
    performance_tier = Column(String(20), nullable=True, index=True)
    match_score = Column(Integer, nullable=True)
    match_reason = Column(Text, nullable=True)

    user = relationship("Registration", back_populates="opportunity_recommendations")
    progress = relationship("UserProgress")
