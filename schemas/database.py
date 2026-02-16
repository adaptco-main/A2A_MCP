from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class ArtifactModel(Base):
    __tablename__ = "artifacts"

    # Use a string UUID for the ID to match the A2A-MCP protocol
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_artifact_id = Column(String, nullable=True)
    agent_name = Column(String, nullable=False)
    version = Column(String, default="1.0.0")
    type = Column(String, nullable=False)  # e.g., 'code', 'test_report'
    content = Column(Text, nullable=False)
    state = Column(String, nullable=True)
    meta_data = Column(Text, nullable=True)  # JSON serialized metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Artifact(id={self.id}, type={self.type}, agent={self.agent_name})>"


class PlanStateModel(Base):
    __tablename__ = "plan_states"

    plan_id = Column(Text, primary_key=True)
    snapshot = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PlanState(plan_id={self.plan_id})>"


class EventModel(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline = Column(String, nullable=False)
    execution_id = Column(String, nullable=False)
    state = Column(String, nullable=False)
    hash = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)  # JSON string

    def __repr__(self):
        return f"<Event(pipeline={self.pipeline}, state={self.state}, execution={self.execution_id})>"
