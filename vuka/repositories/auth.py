from typing import Optional
from sqlalchemy.orm import Session
from vuka.models.registration import Registration

class AuthRepository:
    def __init__(self,db:Session):
        self.db=db

    def _normalize(self,value:str)->str:
        return value.strip().lower()

    def get_by_id(self,user_id:int)->Optional[Registration]:
        return self.db.get(Registration,user_id)

    def get_by_email(self,email:str)->Optional[Registration]:
        normalized_email=self._normalize(email)
        return self.db.query(Registration).filter(Registration.email==normalized_email).first()

    def get_by_username(self,username:str)->Optional[Registration]:
        normalized_username=self._normalize(username)
        return self.db.query(Registration).filter(Registration.username==normalized_username).first()

    def create_user(self,user_obj:Registration)->Registration:
        self.db.add(user_obj)
        self.db.commit()
        self.db.refresh(user_obj)
        return user_obj

    def update_password(self,user:Registration,hashed_password:str)->Registration:
        user.pass_hash=hashed_password
        self.db.commit()
        self.db.refresh(user)
        return user