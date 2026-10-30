import enum
from sqlalchemy import ARRAY, Column, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base


class SocialPlatformEnum(str, enum.Enum):
    tiktok = "tiktok"
    youtube = "youtube"
    instagram = "instagram"
    other = "other"


class Onboarding(Base):
    __tablename__ = "onboarding"

    onboarding_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("registrations.user_id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True,
    )
    user_interests = Column(JSONB, nullable=False)
    social_platforms = Column(ARRAY(Enum(SocialPlatformEnum)), nullable=False)
    user_goal = Column(JSONB, nullable=False)
    career_aspirations = Column(Text, nullable=False)

    registration = relationship("Registration", back_populates="onboarding")
    content_pathways = relationship(
        "ContentPathway", back_populates="onboarding", cascade="all, delete-orphan"
    )
