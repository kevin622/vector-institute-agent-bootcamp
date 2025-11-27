from typing import Optional
from pathlib import Path

from sqlalchemy import create_engine, inspect, Table, MetaData, select
from sqlalchemy.orm import sessionmaker, Session
from langchain.tools import tool


_ENGINE = None  # lazy 생성
SessionLocal = None  # lazy 세션팩토리

# 프로젝트 루트 기준 DB 파일 경로 (현재 파일: tools/db_tool.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "db" / "data.db"


def _get_engine():
    """DB 엔진과 세션팩토리를 초기화하고 반환."""
    global _ENGINE, SessionLocal
    if _ENGINE is None:
        # 디렉터리가 없으면 생성 (SQLite는 상위 디렉터리가 없으면 OperationalError 발생)
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
        SessionLocal = sessionmaker(bind=_ENGINE, expire_on_commit=False, future=True)
    return _ENGINE


def get_session() -> Session:
    """새로운 DB 세션을 반환."""
    if SessionLocal is None:
        _get_engine()
    return SessionLocal()


@tool
def get_tables_from_db() -> list[str]:
    """현재 DB에 존재하는 테이블 이름들을 반환."""
    engine = _get_engine()
    with engine.connect() as conn:
        inspector = inspect(conn)
        return inspector.get_table_names()


@tool
def get_column_info_from_table(table_name: str) -> list[dict]:
    """
    특정 테이블의 컬럼 이름들을 반환.

    Args:
        table_name (str): 컬럼 정보를 가져올 테이블 이름.
    Returns:
        list[dict]: 컬럼 정보 리스트.
    """
    engine = _get_engine()
    with engine.connect() as conn:
        inspector = inspect(conn)
        return inspector.get_columns(table_name)


@tool
def filter_data_by_numeric_condition(
    table_name: str,
    column_name: str,
    gte: Optional[float] = None,
    lte: Optional[float] = None,
) -> list[tuple]:
    """
    특정 테이블의 특정 컬럼에 대해 숫자 조건 필터링을 수행하여 결과 반환.

    Args:
        table_name (str): 필터링할 테이블 이름.
        column_name (str): 필터링할 컬럼 이름.
        gte (Optional[float]): 해당 컬럼의 최소값 조건.
        lte (Optional[float]): 해당 컬럼의 최대값 조건.
    Returns:
        list[tuple]: 필터링된 결과 리스트.
    Raises:
        ValueError: 지정된 컬럼이 테이블에 존재하지 않을 경우.
    """
    engine = _get_engine()
    with engine.connect() as conn:
        inspector = inspect(conn)
        columns = inspector.get_columns(table_name)
        column_names = [col["name"] for col in columns]
        if column_name not in column_names:
            raise ValueError(f"Column '{column_name}' does not exist in table '{table_name}'.")
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)

        stmt = select(table)
        if gte is not None:
            stmt = stmt.where(table.c[column_name] >= gte)
        if lte is not None:
            stmt = stmt.where(table.c[column_name] <= lte)

        result = conn.execute(stmt)
        rows = result.fetchall()
        return rows
