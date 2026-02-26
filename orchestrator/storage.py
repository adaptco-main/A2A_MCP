from __future__ import annotations

import atexit
import json
import os
from typing import Any, Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from schemas.agent_artifacts import MCPArtifact
from schemas.database import ArtifactModel, Base, PlanStateModel

SQLITE_DEFAULT_PATH = "./a2a_mcp.db"


def resolve_database_url() -> str:
    """
    Resolve database URL from explicit URL or profile mode.

    Priority:
    1) DATABASE_URL
    2) DATABASE_MODE=postgres with POSTGRES_* vars
    3) DATABASE_MODE=sqlite with SQLITE_PATH
    """
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url

    database_mode = os.getenv("DATABASE_MODE", "sqlite").strip().lower()
    if database_mode == "postgres":
        user = os.getenv("POSTGRES_USER", "postgres").strip()
        password = os.getenv("POSTGRES_PASSWORD", "pass").strip()
        host = os.getenv("POSTGRES_HOST", "localhost").strip()
        port = os.getenv("POSTGRES_PORT", "5432").strip()
        database = os.getenv("POSTGRES_DB", "mcp_db").strip()
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    sqlite_path = os.getenv("SQLITE_PATH", SQLITE_DEFAULT_PATH).strip() or SQLITE_DEFAULT_PATH
    sqlite_path = sqlite_path.replace("\\", "/")
    return f"sqlite:///{sqlite_path}"


DATABASE_URL = resolve_database_url()


def _build_connect_args(database_url: str) -> dict:
    return {"check_same_thread": False} if "sqlite" in database_url else {}


class DBManager:
    _shared_engine = None
    _shared_session_local = None

    def __init__(self) -> None:
        # Reuse a single engine/sessionmaker across all manager instances.
        if DBManager._shared_engine is None:
            connect_args = _build_connect_args(DATABASE_URL)
            DBManager._shared_engine = create_engine(DATABASE_URL, connect_args=connect_args)
            DBManager._shared_session_local = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=DBManager._shared_engine,
            )
            if os.getenv("ENV") != "production":
                Base.metadata.create_all(bind=DBManager._shared_engine)

        self.engine = DBManager._shared_engine
        self.SessionLocal = DBManager._shared_session_local

    def save_artifact(self, artifact: MCPArtifact) -> ArtifactModel:
        """Save an MCPArtifact to the database."""
        db = self.SessionLocal()
        try:
            db_artifact = ArtifactModel(
                id=artifact.artifact_id,
                parent_artifact_id=getattr(artifact, "parent_artifact_id", artifact.metadata.get('parent_artifact_id') if hasattr(artifact, 'metadata') else None),
                agent_name=getattr(artifact, "agent_name", artifact.metadata.get('agent_name', 'UnknownAgent') if hasattr(artifact, 'metadata') else 'UnknownAgent'),
                version=getattr(artifact, "version", artifact.metadata.get('version', '1.0.0') if hasattr(artifact, 'metadata') else '1.0.0'),
                type=artifact.type,
                content=artifact.content if isinstance(artifact.content, str) else json.dumps(artifact.content),
            )
            db.add(db_artifact)
            db.commit()
            return db_artifact
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactModel]:
        """Retrieve an artifact by ID from the database."""
        db = self.SessionLocal()
        try:
            return db.query(ArtifactModel).filter(ArtifactModel.id == artifact_id).first()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error retrieving artifact {artifact_id}")
            raise
        finally:
            db.close()


_db_manager = DBManager()

# Engine/session for backward compatibility
engine = _db_manager.engine
SessionLocal = _db_manager.SessionLocal


def save_plan_state(plan_id: str, snapshot: Dict[str, Any]) -> None:
    """Save FSM plan state snapshot to the database."""
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

    # Append-only FSM persistence
    try:
        persist_state_machine_snapshot(plan_id, snapshot)
    except Exception:
        # Don't fail the primary save if FSM persistence fails
        pass


def load_plan_state(plan_id: str) -> Optional[Dict[str, Any]]:
    """Load FSM plan state snapshot from the database."""
    from orchestrator.fsm_persistence import load_state_machine_snapshot

    # Try newer FSM persistence first
    try:
        snapshot = load_state_machine_snapshot(plan_id)
        if snapshot is not None:
            return snapshot
    except Exception:
        pass

    db = _db_manager.SessionLocal()
    try:
        state = db.query(PlanStateModel).filter(PlanStateModel.plan_id == plan_id).first()
        if not state:
            return None
        return json.loads(state.snapshot)
    finally:
        db.close()


def _dispose_engine() -> None:
    if DBManager._shared_engine is not None:
        DBManager._shared_engine.dispose()


atexit.register(_dispose_engine)


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
