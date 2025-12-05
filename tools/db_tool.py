from typing import Any, Dict, List, Optional
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


def _error_response(message: str) -> dict[str, str]:
    """표준화된 에러 응답 포맷."""
    return {"error": message}


def _rows_to_table_dicts(rows, column_names: List[str]) -> List[Dict[str, Any]]:
    """Row 객체 리스트를 컬럼 이름 기반 dict 리스트로 변환."""
    formatted_rows: List[Dict[str, Any]] = []
    for row in rows:
        row_values = tuple(row)
        formatted_rows.append({column_names[idx]: row_values[idx] for idx in range(len(column_names))})
    return formatted_rows


def _rows_to_join_dicts(
    rows,
    left_table_name: str,
    left_columns: List[str],
    right_table_name: str,
    right_columns: List[str],
) -> List[Dict[str, Any]]:
    """조인 결과를 테이블별 중첩 dict 형태로 변환."""
    formatted_rows: List[Dict[str, Any]] = []
    left_len = len(left_columns)
    right_len = len(right_columns)

    for row in rows:
        row_values = tuple(row)
        left_values = row_values[:left_len]
        right_values = row_values[left_len : left_len + right_len]

        formatted_rows.append(
            {
                left_table_name: dict(zip(left_columns, left_values)),
                right_table_name: dict(zip(right_columns, right_values)),
            }
        )

    return formatted_rows


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
def get_all_data_from_table(table_name: str) -> dict[str, Any]:
    """
    특정 테이블의 모든 데이터를 반환.

    Args:
        table_name (str): 데이터를 가져올 테이블 이름.
    Returns:
        dict: 테이블, 컬럼, 행 정보를 담은 딕셔너리.
    """
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=engine)

            stmt = select(table)
            result = conn.execute(stmt)
            rows = result.fetchall()
            column_names = [col.name for col in table.c]

            formatted_rows = _rows_to_table_dicts(rows, column_names)

            return {
                "table": table_name,
                "columns": column_names,
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(
            f"Error occurred while getting data from table '{table_name}': {str(e)}"
        )


@tool
def filter_data_by_gte_or_lte(
    table_name: str,
    column_name: str,
    gte: Optional[float] = None,
    lte: Optional[float] = None,
) -> dict[str, Any]:
    """
    특정 테이블의 특정 컬럼에 대해 숫자 조건 필터링을 수행하여 결과 반환.

    Args:
        table_name (str): 필터링할 테이블 이름.
        column_name (str): 필터링할 컬럼 이름.
        gte (Optional[float]): 해당 컬럼의 최소값 조건.
        lte (Optional[float]): 해당 컬럼의 최대값 조건.
    Returns:
        dict: 필터링 조건과 결과를 담은 딕셔너리.
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
            column_names = [col.name for col in table.c]
            formatted_rows = _rows_to_table_dicts(rows, column_names)

            filters: Dict[str, Any] = {
                "column": column_name,
            }
            if gte is not None:
                filters["gte"] = gte
            if lte is not None:
                filters["lte"] = lte

            return {
                "table": table_name,
                "columns": column_names,
                "filters": filters,
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(
            f"Error occurred while filtering data from table '{table_name}': {str(e)}"
        )


@tool
def filter_data_by_inclusion(
    table_name: str,
    column_name: str,
    include_values: list,
) -> dict[str, Any]:
    """
    특정 테이블의 특정 컬럼에 대해 포함 조건 필터링을 수행하여 결과 반환.

    Args:
        table_name (str): 필터링할 테이블 이름.
        column_name (str): 필터링할 컬럼 이름.
        include_values (list): 포함할 값들의 리스트.
    Returns:
        dict: 필터링 조건과 결과를 담은 딕셔너리.
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
            column_names = [col.name for col in table.c]
            formatted_rows = _rows_to_table_dicts(rows, column_names)

            return {
                "table": table_name,
                "columns": column_names,
                "filters": {
                    "column": column_name,
                    "include_values": include_values,
                },
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(
            f"Error occurred while filtering data from table '{table_name}': {str(e)}"
        )


@tool
def filter_data_by_like(
    table_name: str,
    column_name: str,
    like_pattern: str,
) -> dict[str, Any]:
    """
    특정 테이블의 특정 컬럼에 대해 LIKE(부분 문자열) 조건 필터링을 수행하여 결과 반환.

    Args:
        table_name (str): 필터링할 테이블 이름.
        column_name (str): 필터링할 컬럼 이름.
        like_pattern (str): SQL LIKE 패턴(예: '%Research%').
    Returns:
        dict: 필터링 조건과 결과를 담은 딕셔너리.
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
            column_names = [col.name for col in table.c]
            formatted_rows = _rows_to_table_dicts(rows, column_names)

            return {
                "table": table_name,
                "columns": column_names,
                "filters": {
                    "column": column_name,
                    "like": like_pattern,
                },
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(
            f"Error occurred while filtering data from table '{table_name}' with LIKE: {str(e)}"
        )


@tool
def join_tables_on_column(
    left_table: str,
    right_table: str,
    join_column_left: str,
    join_column_right: str,
) -> dict[str, Any]:
    """
    두 테이블을 특정 컬럼을 기준으로 조인하여 결과 반환.

    Args:
        left_table (str): 왼쪽 테이블 이름.
        right_table (str): 오른쪽 테이블 이름.
        join_column (str): 조인할 컬럼 이름.
    Returns:
        dict: 조인 정보와 결과를 담은 딕셔너리.
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
            left_column_names = [col.name for col in left_tbl.c]
            right_column_names = [col.name for col in right_tbl.c]

            formatted_rows = _rows_to_join_dicts(
                rows,
                left_table,
                left_column_names,
                right_table,
                right_column_names,
            )

            return {
                "left_table": left_table,
                "right_table": right_table,
                "columns": {
                    left_table: left_column_names,
                    right_table: right_column_names,
                },
                "join_on": {
                    "left_column": join_column_left,
                    "right_column": join_column_right,
                },
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(
            f"Error occurred while joining tables '{left_table}' and '{right_table}': {str(e)}"
        )
