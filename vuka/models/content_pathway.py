from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class ContentPathway(Base):
    __tablename__ = "content_pathway"
    __table_args__ = (
        UniqueConstraint("onboarding_id", "content_id", name="uq_content_pathway_onboarding_content"),
    )

    content_pathway_id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.content_id", ondelete="CASCADE"), nullable=False, index=True)
    onboarding_id = Column(Integer, ForeignKey("onboarding.onboarding_id", ondelete="CASCADE"), nullable=False, index=True)
    external_media_url = Column(Text, nullable=False)
    media_description = Column(Text, nullable=False)
    date = Column(Date, nullable=False, index=True)
    watched = Column(Boolean, nullable=False, server_default="false", index=True)
    watched_at = Column(DateTime(timezone=True), nullable=True)
    relevance_score = Column(Integer, nullable=True)
    relevance_reason = Column(Text, nullable=True)

    content = relationship("Content", back_populates="content_pathway")
    onboarding = relationship("Onboarding", back_populates="content_pathways")
