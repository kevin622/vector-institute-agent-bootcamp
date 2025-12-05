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
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            inspector = inspect(conn)
            return inspector.get_table_names()
    except Exception as e:
        return f"Error occurred while getting tables: {str(e)}"


@tool
def get_column_info_from_table(table_name: str) -> list[dict]:
    """
    특정 테이블의 컬럼 이름들을 반환.

    Args:
        table_name (str): 컬럼 정보를 가져올 테이블 이름.
    Returns:
        list[dict]: 컬럼 정보 리스트.
    """
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            inspector = inspect(conn)
            return inspector.get_columns(table_name)
    except Exception as e:
        return f"Error occurred while getting column info from table '{table_name}': {str(e)}"


@tool
def filter_data_by_gte_or_lte(
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
    try:
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
    except Exception as e:
        return f"Error occurred while filtering data from table '{table_name}': {str(e)}"


@tool
def filter_data_by_inclusion(
    table_name: str,
    column_name: str,
    include_values: list,
) -> list[tuple]:
    """
    특정 테이블의 특정 컬럼에 대해 포함 조건 필터링을 수행하여 결과 반환.

    Args:
        table_name (str): 필터링할 테이블 이름.
        column_name (str): 필터링할 컬럼 이름.
        include_values (list): 포함할 값들의 리스트.
    Returns:
        list[tuple]: 필터링된 결과 리스트.
    Raises:
        ValueError: 지정된 컬럼이 테이블에 존재하지 않을 경우.
    """
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            inspector = inspect(conn)
            columns = inspector.get_columns(table_name)
            column_names = [col["name"] for col in columns]
            if column_name not in column_names:
                raise ValueError(f"Column '{column_name}' does not exist in table '{table_name}'.")
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=engine)

            stmt = select(table).where(table.c[column_name].in_(include_values))

            result = conn.execute(stmt)
            rows = result.fetchall()
            return rows
    except Exception as e:
        return f"Error occurred while filtering data from table '{table_name}': {str(e)}"


@tool
def filter_data_by_like(
    table_name: str,
    column_name: str,
    like_pattern: str,
) -> list[tuple]:
    """
    특정 테이블의 특정 컬럼에 대해 LIKE(부분 문자열) 조건 필터링을 수행하여 결과 반환.

    Args:
        table_name (str): 필터링할 테이블 이름.
        column_name (str): 필터링할 컬럼 이름.
        like_pattern (str): SQL LIKE 패턴(예: '%Research%').
    Returns:
        list[tuple]: 필터링된 결과 리스트.
    Raises:
        ValueError: 지정된 컬럼이 테이블에 존재하지 않을 경우.
    """
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            inspector = inspect(conn)
            columns = inspector.get_columns(table_name)
            column_names = [col["name"] for col in columns]
            if column_name not in column_names:
                raise ValueError(f"Column '{column_name}' does not exist in table '{table_name}'.")
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=engine)

            stmt = select(table).where(table.c[column_name].like(like_pattern))

            result = conn.execute(stmt)
            rows = result.fetchall()
            return rows
    except Exception as e:
        return f"Error occurred while filtering data from table '{table_name}' with LIKE: {str(e)}"


@tool
def join_tables_on_column(
    left_table: str,
    right_table: str,
    join_column_left: str,
    join_column_right: str,
) -> list[tuple]:
    """
    두 테이블을 특정 컬럼을 기준으로 조인하여 결과 반환.

    Args:
        left_table (str): 왼쪽 테이블 이름.
        right_table (str): 오른쪽 테이블 이름.
        join_column (str): 조인할 컬럼 이름.
    Returns:
        list[tuple]: 조인된 결과 리스트.
    Raises:
        ValueError: 지정된 컬럼이 양쪽 테이블에 존재하지 않을 경우.
    """
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            inspector = inspect(conn)

            left_columns = inspector.get_columns(left_table)
            right_columns = inspector.get_columns(right_table)

            left_column_names = [col["name"] for col in left_columns]
            right_column_names = [col["name"] for col in right_columns]

            if join_column_left not in left_column_names:
                raise ValueError(f"Column '{join_column_left}' does not exist in table '{left_table}'.")
            if join_column_right not in right_column_names:
                raise ValueError(f"Column '{join_column_right}' does not exist in table '{right_table}'.")

            metadata = MetaData()
            left_tbl = Table(left_table, metadata, autoload_with=engine)
            right_tbl = Table(right_table, metadata, autoload_with=engine)

            stmt = select(left_tbl, right_tbl).join(
                right_tbl,
                left_tbl.c[join_column_left] == right_tbl.c[join_column_right],
            )

            result = conn.execute(stmt)
            rows = result.fetchall()
            return rows
    except Exception as e:
        return f"Error occurred while joining tables '{left_table}' and '{right_table}': {str(e)}"
