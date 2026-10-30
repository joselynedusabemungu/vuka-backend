from datetime import datetime, timedelta, timezone

from vuka.repositories.security import SecurityRepository


def record_login(db, user, identifier, ip, success):
    repository = SecurityRepository(db)
    repository.record_login(user, identifier, ip, success)


def recent_ip_failures(db, ip):
    since = datetime.now(timezone.utc) - timedelta(minutes=15)
    repository = SecurityRepository(db)
    return repository.count_recent_ip_failures(ip, since)


def locked(user):
    return (user.failed_login_attempts or 0) >= 5
