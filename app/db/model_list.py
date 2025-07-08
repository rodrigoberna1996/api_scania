from sqlalchemy import Column, Integer, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class SharePointItem(Base):
    __tablename__ = "travel_log"

    id = Column(Integer, primary_key=True, index=True)
    fields = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
