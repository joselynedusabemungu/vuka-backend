from sqlalchemy import Column, DateTime, Integer, Text
from sqlalchemy.orm import relationship

from database import Base


class Content(Base):
    __tablename__ = "content"

    content_id = Column(Integer, primary_key=True, index=True)
    external_media_url = Column(Text, nullable=False, unique=True, index=True)
    source_platform = Column(Text, nullable=False)
    media_description = Column(Text, nullable=False)
    datetime = Column(DateTime, nullable=False)

    content_pathway = relationship("ContentPathway", back_populates="content")
    generated_assessment = relationship(
        "GeneratedAssessment", back_populates="content", uselist=False
    )
