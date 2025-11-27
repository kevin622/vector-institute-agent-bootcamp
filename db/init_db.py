from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
    DateTime,
    Table,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
import random
from typing import Sequence

try:
    from db.sample_data import generate_users, generate_projects
except Exception:
    # Fallback when running as a script from within the `db/` folder
    from sample_data import generate_users, generate_projects  # type: ignore

DB_PATH = Path(__file__).parent / "data.db"
Base = declarative_base()
_ENGINE = None  # lazy 생성
SessionLocal = None  # lazy 세션팩토리


def _get_engine():
    global _ENGINE, SessionLocal
    if _ENGINE is None:
        _ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
        SessionLocal = sessionmaker(bind=_ENGINE, expire_on_commit=False, future=True)
    return _ENGINE


def get_session() -> Session:
    if SessionLocal is None:
        _get_engine()
    return SessionLocal()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    age = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False)

    projects = relationship(
        "Project",
        secondary=lambda: project_users,
        back_populates="users",
    )


project_users = Table(
    "project_users",
    Base.metadata,
    Column("project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    budget = Column(Float)
    created_at = Column(DateTime(timezone=True), nullable=False)

    users = relationship(
        "User",
        secondary=lambda: project_users,
        back_populates="projects",
    )


DEFAULT_USERS_COUNT = 30
DEFAULT_PROJECTS_COUNT = 30


def reset_db() -> None:
    """기존 SQLite 파일 삭제 후 새 테이블 생성 (ID 리셋)."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    engine = _get_engine()
    Base.metadata.create_all(engine)


def insert_data_into_db(users_count: int = DEFAULT_USERS_COUNT, projects_count: int = DEFAULT_PROJECTS_COUNT) -> None:
    """샘플 User/Project 데이터를 삽입. 각 프로젝트에 1~10명의 사용자 연결."""
    random.seed(42)
    now = datetime.now(timezone.utc)
    with get_session() as session:
        user_objs: list[User] = []
        for u in generate_users(users_count):
            user = User(name=u["name"], email=u["email"], age=u["age"], created_at=now)
            session.add(user)
            user_objs.append(user)
        session.flush()

        project_objs: list[Project] = []
        for p in generate_projects(projects_count):
            proj = Project(
                title=p["title"],
                description=p["description"],
                budget=p["budget"],
                created_at=now,
            )
            session.add(proj)
            project_objs.append(proj)

        session.flush()

        max_members = min(10, len(user_objs))
        for proj in project_objs:
            member_count = random.randint(1, max_members)
            members: Sequence[User] = random.sample(user_objs, k=member_count)
            proj.users.extend(members)

        session.commit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reset and seed SQLite DB with sample data.")
    parser.add_argument("--users", type=int, default=DEFAULT_USERS_COUNT, help="Number of users to generate")
    parser.add_argument("--projects", type=int, default=DEFAULT_PROJECTS_COUNT, help="Number of projects to generate")
    args = parser.parse_args()

    reset_db()
    insert_data_into_db(users_count=args.users, projects_count=args.projects)
    print(f"Seeded DB at {DB_PATH} with {args.users} users and {args.projects} projects.")
