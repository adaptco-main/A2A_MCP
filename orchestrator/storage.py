from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schemas.database import Base, ArtifactModel, PlanStateModel
import os
import json
from datetime import datetime, timezone
from typing import Optional

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./a2a_mcp.db")

class DBManager:
    def __init__(self):
        # check_same_thread is required for SQLite
        connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
        self.engine = create_engine(DATABASE_URL, connect_args=connect_args)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def save_artifact(self, artifact):
        db = self.SessionLocal()
        try:
            db_artifact = ArtifactModel(
                id=artifact.artifact_id,
                parent_artifact_id=getattr(artifact, 'parent_artifact_id', None),
                agent_name=getattr(artifact, 'agent_name', 'UnknownAgent'),
                version=getattr(artifact, 'version', '1.0.0'),
                type=artifact.type,
                content=artifact.content
            )
            db.add(db_artifact)
            db.commit()
            return db_artifact
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_artifact(self, artifact_id):
        db = self.SessionLocal()
        try:
            artifact = db.query(ArtifactModel).filter(ArtifactModel.id == artifact_id).first()
            return artifact
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error retrieving artifact {artifact_id}")
            raise
        finally:
            db.close()


_db_manager = DBManager()


def save_plan_state(plan_id: str, snapshot: dict) -> None:
    from orchestrator.fsm_persistence import persist_state_machine_snapshot

    db = _db_manager.SessionLocal()
    try:
        # Backward-compatible latest snapshot cache
        serialized_snapshot = json.dumps(snapshot)
        existing = db.query(PlanStateModel).filter(PlanStateModel.plan_id == plan_id).first()
        if existing:
            existing.snapshot = serialized_snapshot
        else:
            db.add(PlanStateModel(plan_id=plan_id, snapshot=serialized_snapshot))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    # Append-only FSM persistence (event + derived snapshot)
    persist_state_machine_snapshot(plan_id, snapshot)


def load_plan_state(plan_id: str) -> Optional[dict]:
    from orchestrator.fsm_persistence import load_state_machine_snapshot

    snapshot = load_state_machine_snapshot(plan_id)
    if snapshot is not None:
        return snapshot

    db = _db_manager.SessionLocal()
    try:
        state = db.query(PlanStateModel).filter(PlanStateModel.plan_id == plan_id).first()
        if not state:
            return None
        return json.loads(state.snapshot)
    finally:
        db.close()

# Create engine for SessionLocal
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# SessionLocal for backward compatibility (used by mcp_server.py)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
