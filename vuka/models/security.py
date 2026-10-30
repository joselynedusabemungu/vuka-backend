from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from database import Base


class LoginAttempt(Base):
    __tablename__="login_attempts"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("registrations.user_id",ondelete="CASCADE"),nullable=True,index=True)
    identifier=Column(String(255),nullable=False,index=True)
    ip_address=Column(String(64),nullable=True)
    success=Column(Boolean,nullable=False,default=False)
    attempted_at=Column(DateTime(timezone=True),server_default=func.now(),nullable=False,index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("registrations.user_id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(80), nullable=False, index=True)
    action = Column(String(120), nullable=False)
    target_type = Column(String(80), nullable=True)
    target_id = Column(String(80), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=True)


class SecurityEvent(Base):
    __tablename__ = "security_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("registrations.user_id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(80), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="LOW")
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class SecurityAlert(Base):
    __tablename__ = "security_alerts"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("security_events.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(80), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("registrations.user_id", ondelete="SET NULL"), nullable=True)


class VerificationDocument(Base):
    __tablename__ = "verification_documents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("registrations.user_id", ondelete="CASCADE"), nullable=False, index=True)
    document_reference = Column(String(512), nullable=False, unique=True)
    document_type = Column(String(80), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(120), nullable=False)
    verification_status = Column(String(30), nullable=False, default="PENDING", index=True)
    rejection_reason = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("registrations.user_id", ondelete="SET NULL"), nullable=True)
