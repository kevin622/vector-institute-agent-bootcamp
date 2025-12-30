from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from sqlalchemy import Date, DateTime, MetaData, Table, create_engine, inspect, select
from sqlalchemy.sql import sqltypes
from sqlalchemy.orm import sessionmaker, Session
from langchain.tools import tool

_ENGINE = None  # lazy 생성
SessionLocal = None  # lazy 세션팩토리

# 반환 결과에 적용할 기본 최대 행 수 (대량 데이터로 인한 OOM 및 프롬프트가 너무 길어지는 문제 방지)
DEFAULT_ROW_LIMIT = 50

# 프로젝트 루트 기준 DB 파일 경로 (현재 파일: tools/db_tool.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "db" / "movie.db"


def _get_engine():
    """DB 엔진과 세션팩토리를 초기화하고 반환."""
    global _ENGINE, SessionLocal
    if _ENGINE is None:
        # 디렉터리가 없으면 생성 (SQLite는 상위 디렉터리가 없으면 OperationalError 발생)
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
        SessionLocal = sessionmaker(bind=_ENGINE, expire_on_commit=False, future=True)
    return _ENGINE


def _error_response(message: str) -> dict[str, str]:
    """표준화된 에러 응답 포맷."""
    return {"error": message}


def _rows_to_table_dicts(rows, column_names: List[str]) -> List[Dict[str, Any]]:
    """Row 객체 리스트를 컬럼 이름 기반 dict 리스트로 변환."""
    formatted_rows: List[Dict[str, Any]] = []
    for row in rows:
        row_mapping = row._mapping if hasattr(row, "_mapping") else dict(row)
        formatted_rows.append({col: row_mapping.get(col) for col in column_names})
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


def _resolve_limit(limit: Optional[int]) -> int:
    """요청된 limit을 정리한다. 0 이하는 무시하고 기본값 사용."""
    if limit is None or limit <= 0:
        return DEFAULT_ROW_LIMIT
    return limit


def _normalize_bound_value(column, value: Any) -> Any:
    """컬럼 타입에 맞춰 gte/lte 값을 변환한다."""
    if value is None:
        return None

    col_type = column.type

    if isinstance(col_type, Date):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("Date must be ISO format (YYYY-MM-DD).") from exc
        raise ValueError("Value must be date, datetime, or ISO date string for Date column.")

    if isinstance(col_type, DateTime):
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError as exc:
                raise ValueError("Datetime must be ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).") from exc
        raise ValueError("Value must be datetime, date, or ISO datetime string for DateTime column.")

    if isinstance(col_type, (sqltypes.Integer, sqltypes.Numeric, sqltypes.Float)):
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError as exc:
                raise ValueError("Numeric filter must be convertible to float.") from exc
        raise ValueError("Value must be numeric or numeric string for numeric column.")

    return value


def _resolve_ordering(table, order_by: Optional[List[str]] = None) -> tuple[list, list, List[str]]:
    """정렬 기준을 구문분석한다. 우선순위: 사용자 지정 → PK → 첫 번째 컬럼."""
    orders = []
    not_null_cols = []
    display: List[str] = []

    if order_by:
        for raw in order_by:
            parts = raw.split()
            col_name = parts[0]
            direction = parts[1].lower() if len(parts) > 1 else "asc"
            if col_name in table.c:
                col = table.c[col_name]
                not_null_cols.append(col)
                if direction == "desc":
                    orders.append(col.desc())
                    display.append(f"{col_name} desc")
                else:
                    orders.append(col.asc())
                    display.append(f"{col_name} asc")
        if orders:
            return orders, not_null_cols, display

    pk_cols = list(table.primary_key.columns)
    if pk_cols:
        orders = [col.asc() for col in pk_cols]
        not_null_cols = pk_cols
        display = [f"{col.name} asc" for col in pk_cols]
        return orders, not_null_cols, display

    first_col = next(iter(table.c))
    return [first_col.asc()], [first_col], [f"{first_col.name} asc"]


def _apply_not_null_filters(stmt, columns):
    """정렬 기준 컬럼 값이 None인 행은 제외한다."""
    for col in columns:
        stmt = stmt.where(col.is_not(None))
    return stmt


def get_tables_from_db() -> list[str]:
    """
    현재 DB에 존재하는 테이블 이름들을 반환.
    (추가) tool로 사용하기보단 에이전트 초기화 시점에 메타정보 확인용으로 사용.
    """
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
def get_top_n_data_from_table(
    table_name: str,
    column_names: Optional[List[str]] = None,
    limit: Optional[int] = DEFAULT_ROW_LIMIT,
    order_by: Optional[List[str]] = None,
) -> dict[str, Any]:
    """
    특정 테이블의 상위 N개 데이터를 반환.

    Args:
        table_name (str): 데이터를 가져올 테이블 이름.
        column_names (Optional[List[str]]): 반환할 컬럼 이름 리스트. 지정하지 않으면 모든 컬럼 반환.
        limit (Optional[int]): 반환할 최대 행 수.
        order_by (Optional[List[str]]): 정렬 기준 리스트. 항목은 "{컬럼명}" 또는 "{컬럼명} {asc|desc}" 형식. 지정하지 않으면 PK 또는 첫 번째 컬럼 기준 오름차순.
    Returns:
        dict: 테이블, 컬럼, 행 정보를 담은 딕셔너리.
    """
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=engine)

            resolved_limit = _resolve_limit(limit)
            order_exprs, not_null_cols, order_display = _resolve_ordering(table, order_by)
            stmt = select(table)
            stmt = _apply_not_null_filters(stmt, not_null_cols)
            stmt = stmt.order_by(*order_exprs).limit(resolved_limit)
            result = conn.execute(stmt)
            rows = result.fetchall()
            table_column_names = [col.name for col in table.c]
            if column_names is None:
                column_names = table_column_names
            else:
                invalid_columns = [col for col in column_names if col not in table_column_names]
                if invalid_columns:
                    return _error_response(f"Columns {invalid_columns} do not exist in table '{table_name}'.")

            formatted_rows = _rows_to_table_dicts(rows, column_names)

            return {
                "table": table_name,
                "columns": column_names,
                "limit": resolved_limit,
                "order_by": order_display,
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(f"Error occurred while getting data from table '{table_name}': {str(e)}")


@tool
def filter_data_by_gte_or_lte(
    table_name: str,
    column_name: str,
    gte: Optional[Union[int, float, str, date, datetime]] = None,
    lte: Optional[Union[int, float, str, date, datetime]] = None,
    limit: Optional[int] = DEFAULT_ROW_LIMIT,
    order_by: Optional[List[str]] = None,
) -> dict[str, Any]:
    """
    특정 테이블의 특정 컬럼에 대해 숫자 또는 날짜/시간 조건 필터링을 수행하여 결과 반환.

    Args:
        table_name (str): 필터링할 테이블 이름.
        column_name (str): 필터링할 컬럼 이름.
        gte (Optional[Union[int, float, str, date, datetime]]): 최소값/최소일 조건. ISO 문자열 또는 date/datetime 허용.
        lte (Optional[Union[int, float, str, date, datetime]]): 최대값/최대일 조건. ISO 문자열 또는 date/datetime 허용.
        limit (Optional[int]): 반환할 최대 행 수.
        order_by (Optional[List[str]]): 정렬 기준 리스트. 항목은 "{컬럼명}" 또는 "{컬럼명} {asc|desc}" 형식. 지정하지 않으면 PK 또는 첫 번째 컬럼 기준 오름차순.
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
            column = table.c[column_name]

            normalized_gte = _normalize_bound_value(column, gte)
            normalized_lte = _normalize_bound_value(column, lte)

            resolved_limit = _resolve_limit(limit)
            order_exprs, not_null_cols, order_display = _resolve_ordering(table, order_by)
            stmt = select(table)
            stmt = _apply_not_null_filters(stmt, not_null_cols)
            stmt = stmt.order_by(*order_exprs)
            if normalized_gte is not None:
                stmt = stmt.where(column >= normalized_gte)
            if normalized_lte is not None:
                stmt = stmt.where(column <= normalized_lte)
            stmt = stmt.limit(resolved_limit)

            result = conn.execute(stmt)
            rows = result.fetchall()
            column_names = [col.name for col in table.c]
            formatted_rows = _rows_to_table_dicts(rows, column_names)

            filters: Dict[str, Any] = {
                "column": column_name,
            }
            if normalized_gte is not None:
                filters["gte"] = (
                    normalized_gte.isoformat() if isinstance(normalized_gte, (date, datetime)) else normalized_gte
                )
            if normalized_lte is not None:
                filters["lte"] = (
                    normalized_lte.isoformat() if isinstance(normalized_lte, (date, datetime)) else normalized_lte
                )

            return {
                "table": table_name,
                "columns": column_names,
                "filters": filters,
                "limit": resolved_limit,
                "order_by": order_display,
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(f"Error occurred while filtering data from table '{table_name}': {str(e)}")


@tool
def filter_data_by_inclusion(
    table_name: str,
    column_name: str,
    include_values: list,
    limit: Optional[int] = DEFAULT_ROW_LIMIT,
    order_by: Optional[List[str]] = None,
) -> dict[str, Any]:
    """
    특정 테이블의 특정 컬럼에 대해 포함 조건 필터링을 수행하여 결과 반환.

    Args:
        table_name (str): 필터링할 테이블 이름.
        column_name (str): 필터링할 컬럼 이름.
        include_values (list): 포함할 값들의 리스트.
        limit (Optional[int]): 반환할 최대 행 수.
        order_by (Optional[List[str]]): 정렬 기준 리스트. 항목은 "{컬럼명}" 또는 "{컬럼명} {asc|desc}" 형식. 지정하지 않으면 PK 또는 첫 번째 컬럼 기준 오름차순.
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

            resolved_limit = _resolve_limit(limit)
            order_exprs, not_null_cols, order_display = _resolve_ordering(table, order_by)
            stmt = (
                select(table)
                .where(table.c[column_name].in_(include_values))
                .order_by(*order_exprs)
                .limit(resolved_limit)
            )
            stmt = _apply_not_null_filters(stmt, not_null_cols)

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
                "limit": resolved_limit,
                "order_by": order_display,
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(f"Error occurred while filtering data from table '{table_name}': {str(e)}")


@tool
def filter_data_by_like(
    table_name: str,
    column_name: str,
    like_pattern: str,
    limit: Optional[int] = DEFAULT_ROW_LIMIT,
    order_by: Optional[List[str]] = None,
) -> dict[str, Any]:
    """
    특정 테이블의 특정 컬럼에 대해 LIKE(부분 문자열) 조건 필터링을 수행하여 결과 반환.

    Args:
        table_name (str): 필터링할 테이블 이름.
        column_name (str): 필터링할 컬럼 이름.
        like_pattern (str): SQL LIKE 패턴(예: '%Research%').
        limit (Optional[int]): 반환할 최대 행 수.
        order_by (Optional[List[str]]): 정렬 기준 리스트. 항목은 "{컬럼명}" 또는 "{컬럼명} {asc|desc}" 형식. 지정하지 않으면 PK 또는 첫 번째 컬럼 기준 오름차순.
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

            resolved_limit = _resolve_limit(limit)
            order_exprs, not_null_cols, order_display = _resolve_ordering(table, order_by)
            stmt = (
                select(table)
                .where(table.c[column_name].like(like_pattern))
                .order_by(*order_exprs)
                .limit(resolved_limit)
            )
            stmt = _apply_not_null_filters(stmt, not_null_cols)

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
                "limit": resolved_limit,
                "order_by": order_display,
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(f"Error occurred while filtering data from table '{table_name}' with LIKE: {str(e)}")


@tool
def join_tables_on_column(
    left_table: str,
    right_table: str,
    join_column_left: str,
    join_column_right: str,
    limit: Optional[int] = DEFAULT_ROW_LIMIT,
    order_by: Optional[List[str]] = None,
) -> dict[str, Any]:
    """
    두 테이블을 특정 컬럼을 기준으로 조인하여 결과 반환.

    Args:
        left_table (str): 왼쪽 테이블 이름.
        right_table (str): 오른쪽 테이블 이름.
        join_column_left (str): 왼쪽 테이블에서 조인할 컬럼 이름.
        join_column_right (str): 오른쪽 테이블에서 조인할 컬럼 이름.
        limit (Optional[int]): 반환할 최대 행 수.
        order_by (Optional[List[str]]): 정렬 기준 리스트(왼쪽 테이블 기준). 항목은 "{컬럼명}" 또는 "{컬럼명} {asc|desc}" 형식. 지정하지 않으면 PK 또는 첫 번째 컬럼 기준 오름차순.
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

            resolved_limit = _resolve_limit(limit)
            order_exprs, not_null_cols, order_display = _resolve_ordering(left_tbl, order_by)
            stmt = (
                select(left_tbl, right_tbl)
                .join(
                    right_tbl,
                    left_tbl.c[join_column_left] == right_tbl.c[join_column_right],
                )
                .order_by(*order_exprs)
                .limit(resolved_limit)
            )
            stmt = _apply_not_null_filters(stmt, not_null_cols)

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
                "limit": resolved_limit,
                "order_by": order_display,
                "row_count": len(formatted_rows),
                "rows": formatted_rows,
            }
    except Exception as e:
        return _error_response(f"Error occurred while joining tables '{left_table}' and '{right_table}': {str(e)}")


@tool
def get_unique_values_of_columns(
    table_name: str,
    column_names: List[str],
    limit: Optional[int] = DEFAULT_ROW_LIMIT,
) -> dict[str, Any]:
    """
    특정 테이블의 여러 컬럼에 대해 고유 값들을 반환.

    Args:
        table_name (str): 데이터를 가져올 테이블 이름.
        column_names (List[str]): 고유 값을 가져올 컬럼 이름 리스트.
        limit (Optional[int]): 각 컬럼별로 반환할 최대 고유 값 수.
    Returns:
        dict: 컬럼별 고유 값 리스트를 담은 딕셔너리.
    """
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=engine)

            resolved_limit = _resolve_limit(limit)
            unique_values: Dict[str, List[Any]] = {}
            for col_name in column_names:
                if col_name not in table.c:
                    return _error_response(f"Column '{col_name}' does not exist in table '{table_name}'.")
                stmt = (
                    select(table.c[col_name])
                    .where(table.c[col_name].is_not(None))
                    .distinct()
                    .order_by(table.c[col_name])
                    .limit(resolved_limit)
                )
                result = conn.execute(stmt)
                rows = result.fetchall()
                unique_values[col_name] = [row[0] for row in rows]

            return {
                "table": table_name,
                "unique_values": unique_values,
                "limit": resolved_limit,
            }
    except Exception as e:
        return _error_response(f"Error occurred while getting unique values from table '{table_name}': {str(e)}")
