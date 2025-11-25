from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

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

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    budget = Column(Float)
    created_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="projects")


USERS_SAMPLE: list[dict] = [
    {"name": "김지현", "email": "jihyun.kim@example.com", "age": 29},
    {"name": "이도현", "email": "dohyun.lee@example.com", "age": 34},
    {"name": "박서준", "email": "seojun.park@example.com", "age": 41},
    {"name": "최민아", "email": "mina.choi@example.com", "age": 27},
    {"name": "정우성", "email": "woosung.jung@example.com", "age": 45},
    {"name": "한지원", "email": "jiwon.han@example.com", "age": 32},
    {"name": "서하늘", "email": "haneul.seo@example.com", "age": 38},
    {"name": "오예린", "email": "yerin.oh@example.com", "age": 30},
    {"name": "장태현", "email": "taehyun.jang@example.com", "age": 36},
    {"name": "윤세아", "email": "seah.yoon@example.com", "age": 28},
]

PROJECTS_SAMPLE: list[dict] = [
    {
        "title": "사내 일정 통합 플랫폼",
        "description": "캘린더/회의실/근태 통합 웹 서비스",
        "budget": 7500.0,
        "user_index": 0,
    },
    {
        "title": "머신러닝 모델 서빙 개선",
        "description": "GPU 자원 효율화 및 자동 스케일링",
        "budget": 12000.0,
        "user_index": 2,
    },
    {
        "title": "고객 대시보드 리뉴얼",
        "description": "React 기반 UI 재설계 및 접근성 향상",
        "budget": 6400.0,
        "user_index": 1,
    },
    {
        "title": "ETL 파이프라인 안정화",
        "description": "데이터 중복 제거와 지연 시간 단축",
        "budget": 9300.0,
        "user_index": 3,
    },
    {
        "title": "사내 인증 시스템 고도화",
        "description": "OIDC + MFA 도입 및 레거시 정리",
        "budget": 10500.0,
        "user_index": 4,
    },
    {
        "title": "데이터 카탈로그 구축",
        "description": "메타데이터 검색 및 품질 지표 제공",
        "budget": 8800.0,
        "user_index": 6,
    },
    {"title": "오브저버빌리티 개선", "description": "로그/트레이스/메트릭 일원화", "budget": 7000.0, "user_index": 5},
    {"title": "AB 테스트 자동화", "description": "실험 설정/분석 파이프라인 자동화", "budget": 5600.0, "user_index": 7},
    {
        "title": "데이터 레이크 비용 최적화",
        "description": "저빈도 데이터 아카이빙 전략 적용",
        "budget": 9900.0,
        "user_index": 8,
    },
    {
        "title": "CI/CD 파이프라인 병렬화",
        "description": "빌드 속도 단축 및 캐시 정책 개선",
        "budget": 8500.0,
        "user_index": 9,
    },
]


def reset_db() -> None:
    """기존 SQLite 파일 삭제 후 새 테이블 생성 (ID 리셋)."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    engine = _get_engine()
    Base.metadata.create_all(engine)


def insert_data_into_db() -> None:
    """샘플 User/Project 데이터를 삽입."""
    now = datetime.now(timezone.utc)
    with get_session() as session:
        user_objs: list[User] = []
        for u in USERS_SAMPLE:
            user = User(name=u["name"], email=u["email"], age=u["age"], created_at=now)
            session.add(user)
            user_objs.append(user)
        session.flush()  # user_ids 확보
        for p in PROJECTS_SAMPLE:
            owner = user_objs[p["user_index"]]
            proj = Project(
                user_id=owner.id,
                title=p["title"],
                description=p["description"],
                budget=p["budget"],
                created_at=now,
            )
            session.add(proj)
        session.commit()


if __name__ == "__main__":
    reset_db()
    insert_data_into_db()
