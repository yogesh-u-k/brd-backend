from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)
    token_id = Column(String, nullable=True)
    jira_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
