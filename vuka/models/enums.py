import enum
class CategoryEnum(str, enum.Enum):
    TECHNICAL_SKILLS = "technical_skills"
    SOFT_SKILLS = "soft_skills"
    CAREER_READINESS = "career_readiness"
    DIGITAL_LITERACY = "digital_literacy"

class GenderEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class UserTypeEnum(str, enum.Enum):
    STUDENT = "student"
    GRADUATE = "highschool_graduate"

class SubjectFieldEnum(str, enum.Enum):
    TECH = "tech"
    FINTECH = "fintech"
    ENGINEERING = "engineering"
    BUSINESS = "business"
    HEALTHCARE = "healthcare"
    CREATIVE_ARTS = "creative_arts"
    OTHER = "other"