from sqlalchemy import Column, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, UTC

Base = declarative_base()


class SharePointItem(Base):
    __tablename__ = "travel_log"

    id = Column(Integer, primary_key=True, index=True)
    fields = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    modified_at = Column(DateTime(timezone=True), default=datetime.now(UTC), onupdate=datetime.now(UTC))


class SharePointReassignmentsItem(Base):
    __tablename__ = "reassignments"

    id = Column(Integer, primary_key=True, index=True)
    fields = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    modified_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
