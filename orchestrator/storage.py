from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schemas.database import Base, ArtifactModel, PlanStateModel
import os
import json
from typing import Optional

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
    def __init__(self):
        # check_same_thread is required for SQLite
        connect_args = _build_connect_args(DATABASE_URL)
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
    db = _db_manager.SessionLocal()
    try:
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


def load_plan_state(plan_id: str) -> Optional[dict]:
    db = _db_manager.SessionLocal()
    try:
        state = db.query(PlanStateModel).filter(PlanStateModel.plan_id == plan_id).first()
        if not state:
            return None
        return json.loads(state.snapshot)
    finally:
        db.close()


# Create engine for SessionLocal
connect_args = _build_connect_args(DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# SessionLocal for backward compatibility (used by mcp_server.py)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
