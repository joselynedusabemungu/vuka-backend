from sqlalchemy.orm import Session
from vuka.models.contents import Content


class ContentRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = Content

    def get_by_id(self, content_id: int):
        return self.db.get(self.model, content_id)

    def get_by_url(self, external_media_url: str):
        return self.db.query(self.model).filter(self.model.external_media_url == external_media_url).first()

    def get_all(self, skip: int = 0, limit: int = 50):
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, data: dict) -> Content:
        record = self.model(**data)
        self.db.add(record)
        self.db.flush()
        return record

    def update(self, content_id: int, data: dict):
        record = self.get_by_id(content_id)
        if not record:
            return None
        for key, value in data.items():
            setattr(record, key, value)
        self.db.flush()
        return record

    def delete(self, content_id: int) -> bool:
        record = self.get_by_id(content_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.flush()
        return True
