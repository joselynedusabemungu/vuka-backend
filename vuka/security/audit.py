import json
from sqlalchemy.orm import Session
from vuka.models.security import AuditLog, SecurityEvent, SecurityAlert


def record_event(db: Session, *, event_type: str, action: str, user_id=None, target_type=None,
                 target_id=None, ip_address=None, user_agent=None, success=True, metadata=None,
                 severity="LOW", alert=False):
    audit = AuditLog(user_id=user_id, event_type=event_type, action=action, target_type=target_type,
                     target_id=str(target_id) if target_id is not None else None, ip_address=ip_address,
                     user_agent=user_agent, success=success,
                     metadata_json=json.dumps(metadata or {}, default=str))
    event = SecurityEvent(user_id=user_id, event_type=event_type, severity=severity,
                          ip_address=ip_address, user_agent=user_agent,
                          details=json.dumps(metadata or {}, default=str))
    db.add(audit); db.add(event); db.flush()
    if alert:
        db.add(SecurityAlert(event_id=event.id, alert_type=event_type, severity=severity))
    db.commit()
    return event
