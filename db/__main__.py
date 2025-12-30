"""SQLite loader for movie and person JSON dumps.
x
New requirements
----------------
- Every key that appears in the sample JSON files must have a matching column.
- People and movies keep their own tables; directors/actors/staffs reference
  People through bridge tables instead of standalone tables.
- Dates are stored as ``DATE`` columns when they can be parsed; the original
  string is preserved alongside when needed.
- ``ccube_contents`` is intentionally ignored.

Usage
-----
python -m db
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import sessionmaker

from db.utils import chunked, clean_text, normalize_json_list, parse_date_field, parse_int
from db.models import Base, Movie, MoviePersonRole, Expert, MovieExpert, Person

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_role_rows(
    session,
    movie_code: str,
    people: Iterable[Dict[str, Any]],
    role_type: str,
    id_key: str,
    *,
    extract_extras: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    skip_missing_id: bool = True,
) -> List[Dict[str, Any]]:
    """Create bridge-table rows for directors/actors/staff while ensuring FK safety."""

    rows: List[Dict[str, Any]] = []
    extract = extract_extras or (lambda _: {})

    for person_stub in people:
        ensure_person(session, person_stub)
        person_id = clean_text(person_stub.get(id_key))
        if skip_missing_id and not person_id:
            continue

        row = {"movie_code": movie_code, "person_id": person_id, "role_type": role_type}
        row.update(extract(person_stub))
        rows.append(row)

    return rows


def _actor_extras(person_stub: Dict[str, Any]) -> Dict[str, Any]:
    """Collect actor-specific role metadata."""

    return {
        "actor_role": clean_text(person_stub.get("actorRole")),
        "actor_classification": clean_text(person_stub.get("actorGb")),
    }


def _staff_extras(person_stub: Dict[str, Any]) -> Dict[str, Any]:
    """Collect staff-specific role metadata."""

    return {"staff_role": clean_text(person_stub.get("staffRole"))}


def _collect_expert_rows(
    movie_code: str, experts: Iterable[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Build Expert and MovieExpert rows for batch insertion."""

    expert_rows: List[Dict[str, Any]] = []
    movie_expert_rows: List[Dict[str, Any]] = []

    for expert in experts:
        expert_id = clean_text(expert.get("expertId"))
        if not expert_id:
            continue

        expert_rows.append(
            {
                "expert_id": expert_id,
                "expert_name": clean_text(expert.get("expertNm")),
                "expert_name_en": clean_text(expert.get("expertNameEng")),
            }
        )
        movie_expert_rows.append(
            {
                "movie_code": movie_code,
                "expert_id": expert_id,
                "expert_point": clean_text(expert.get("expertPoint")),
                "expert_comment": clean_text(expert.get("expertComment")),
            }
        )

    return expert_rows, movie_expert_rows


# ---------------------------------------------------------------------------
# JSON iterators
# ---------------------------------------------------------------------------


def iter_movies(path: Path, limit: Optional[int], force_no_stream: bool = False) -> Iterable[Dict[str, Any]]:
    """Yield movie dicts; uses ijson when available for large files."""

    if not force_no_stream:
        try:
            import ijson

            with path.open("r", encoding="utf-8") as f:
                for idx, movie in enumerate(ijson.items(f, "MovieList.item")):
                    if limit and idx >= limit:
                        break
                    yield movie
            return
        except ImportError:
            pass

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    movies = data.get("MovieList", [])
    if limit:
        movies = movies[:limit]
    for movie in movies:
        yield movie


def iter_people(path: Path, limit: Optional[int]) -> Iterable[Dict[str, Any]]:
    """Yield person dicts from the people JSON dump."""

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    people = data.get("PeopleList") or data.get("people") or []
    if limit:
        people = people[:limit]
    for person in people:
        yield person


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------


def convert_person_record(person: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw person JSON object into a DB-ready row."""

    birth_date, birth_raw = parse_date_field(person.get("birthDt"))
    death_date, death_raw = parse_date_field(person.get("deathDt"))
    updated_at, updated_raw = parse_date_field(person.get("updateDt"))

    return {
        "person_id": clean_text(person.get("personId")),
        "person_name": clean_text(person.get("personNm")),
        "person_name_en": clean_text(person.get("personEngNm")),
        "origin_name": clean_text(person.get("originNm")),
        "native_name": clean_text(person.get("nativeNm")),
        "ect_name": clean_text(person.get("ectNm")),
        "country_name": clean_text(person.get("countryNm")),
        "birth_date": birth_date,
        "birth_date_raw": birth_raw,
        "death_date": death_date,
        "death_date_raw": death_raw,
        "job_name": clean_text(person.get("jobNm")),
        "sub_job_name": clean_text(person.get("subJobNm")),
        "sex": clean_text(person.get("sexVal")),
        "height": clean_text(person.get("hegtval")),
        "weight": clean_text(person.get("wgtval")),
        "education": clean_text(person.get("education")),
        "hobby": clean_text(person.get("hobyNm")),
        "remark": clean_text(person.get("remrkNm")),
        "company": clean_text(person.get("posCmpnNm")),
        "official_site": clean_text(person.get("officialSite")),
        "image_url": clean_text(person.get("imgFileURL")),
        "age": clean_text(person.get("age")),
        "zodiac": clean_text(person.get("zodiac")),
        "constellation": clean_text(person.get("constellation")),
        "updated_at": updated_at,
        "updated_at_raw": updated_raw,
        "awards": normalize_json_list(person.get("Awards")),
        "awards_top3": normalize_json_list(person.get("Awards_Top3")),
        "directors_filmography_top5": normalize_json_list(person.get("Directors_Filmography_Top5")),
        "actors_filmography_top5": normalize_json_list(person.get("Actors_Filmography_Top5")),
        "filmography_top5": normalize_json_list(person.get("Filmography_Top5")),
        "filmography": normalize_json_list(person.get("Filmography")),
        "rel_person": normalize_json_list(person.get("RelPerson")),
    }


def ensure_person(session, person_stub: Dict[str, Any]) -> None:
    """Upsert minimal person info so FK constraints succeed."""

    person_id = clean_text(
        person_stub.get("personId")
        or person_stub.get("directorId")
        or person_stub.get("actorId")
        or person_stub.get("staffId")
    )
    if not person_id:
        return

    exists = session.execute(select(Person.person_id).where(Person.person_id == person_id)).scalar_one_or_none()
    if exists:
        return

    row = {
        "person_id": person_id,
        "person_name": clean_text(
            person_stub.get("personNm")
            or person_stub.get("directorNm")
            or person_stub.get("actorNm")
            or person_stub.get("staffNm")
        ),
        "person_name_en": clean_text(
            person_stub.get("personNmEn")
            or person_stub.get("directorNmEn")
            or person_stub.get("actorNmEn")
            or person_stub.get("personEngNm")
        ),
    }
    session.execute(insert(Person).prefix_with("OR IGNORE"), [row])


def convert_movie_record(movie: Dict[str, Any]) -> Dict[str, Any]:
    """Split a raw movie JSON object into movie and related role payloads."""

    open_date, open_raw = parse_date_field(movie.get("openDt"))

    return {
        "movie": {
            "movie_code": clean_text(movie.get("movieCd")),
            "movie_name": clean_text(movie.get("movieNm")),
            "movie_name_en": clean_text(movie.get("movieNmEn")),
            "movie_name_org": clean_text(movie.get("movieNmOg")),
            "show_time": clean_text(movie.get("showTm")),
            "product_year": clean_text(movie.get("prdtYear")),
            "open_date": open_date,
            "open_date_raw": open_raw,
            "watch_grade_name": clean_text(movie.get("watchGradeNm")),
            "synopsis": clean_text(movie.get("synops")),
            "audience_count": parse_int(movie.get("audiCnt") or movie.get("acdiCnt")),
            "type_name": clean_text(movie.get("typeNm")),
            "nations": normalize_json_list(movie.get("nations")),
            "genres": normalize_json_list(movie.get("genres")),
            "companys": normalize_json_list(movie.get("companys")),
            "cine21_cd": clean_text(movie.get("cine21Cd")),
            "awards": normalize_json_list(movie.get("awardsNm")),
            "awards_top3": normalize_json_list(movie.get("awards_top3")),
        },
        "directors": movie.get("directors", []),
        "actors": movie.get("actors", []),
        "staffs": movie.get("staffs", []),
        "experts": movie.get("experts", []),
    }


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def reset_db(engine) -> None:
    """Drop and recreate all tables for a clean load."""

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def _make_engine(db_path: Path):
    """Build a SQLite engine with JSON support preserved."""

    return create_engine(
        f"sqlite:///{db_path}",
        future=True,
        json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
        json_deserializer=lambda data: json.loads(data),
    )


def load_people_into_db(people_path: Path, db_path: Path, batch_size: int = 1000, limit: Optional[int] = None) -> None:
    """Bulk-load people records into SQLite in batches."""

    engine = _make_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    people_iter = iter_people(people_path, limit=limit)
    batches = chunked(people_iter, batch_size)

    with Session() as session:
        for batch_idx, people_batch in enumerate(batches, start=1):
            person_rows: List[Dict[str, Any]] = []
            for person in people_batch:
                row = convert_person_record(person)
                if not row.get("person_id"):
                    continue
                person_rows.append(row)

            if person_rows:
                session.execute(insert(Person).prefix_with("OR REPLACE"), person_rows)
                session.commit()

            processed = batch_idx * batch_size
            if limit:
                processed = min(processed, limit)
            print(f"Committed people batch {batch_idx} (people processed: {processed})")


def load_movies_into_db(
    movie_path: Path,
    db_path: Path,
    batch_size: int = 1000,
    limit: Optional[int] = None,
    force_no_stream: bool = False,
) -> None:
    """Bulk-load movies plus related role/expert bridges into SQLite."""

    engine = _make_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    movie_iter = iter_movies(movie_path, limit=limit, force_no_stream=force_no_stream)
    batches = chunked(movie_iter, batch_size)

    with Session() as session:
        for batch_idx, movies_batch in enumerate(batches, start=1):
            movie_rows: List[Dict[str, Any]] = []
            role_rows: List[Dict[str, Any]] = []
            expert_rows: List[Dict[str, Any]] = []
            movie_expert_rows: List[Dict[str, Any]] = []

            for movie in movies_batch:
                payload = convert_movie_record(movie)
                movie_row = payload["movie"]
                if not movie_row.get("movie_code"):
                    continue

                role_rows.extend(
                    _build_role_rows(
                        session=session,
                        movie_code=movie_row["movie_code"],
                        people=payload["directors"],
                        role_type="director",
                        id_key="directorId",
                        skip_missing_id=False,
                    )
                )
                role_rows.extend(
                    _build_role_rows(
                        session=session,
                        movie_code=movie_row["movie_code"],
                        people=payload["actors"],
                        role_type="actor",
                        id_key="actorId",
                        extract_extras=_actor_extras,
                    )
                )
                role_rows.extend(
                    _build_role_rows(
                        session=session,
                        movie_code=movie_row["movie_code"],
                        people=payload["staffs"],
                        role_type="staff",
                        id_key="staffId",
                        extract_extras=_staff_extras,
                    )
                )

                expert_batch, movie_expert_batch = _collect_expert_rows(movie_row["movie_code"], payload["experts"])
                expert_rows.extend(expert_batch)
                movie_expert_rows.extend(movie_expert_batch)

                movie_rows.append(movie_row)

            if movie_rows:
                session.execute(insert(Movie).prefix_with("OR REPLACE"), movie_rows)
            if role_rows:
                session.execute(insert(MoviePersonRole).prefix_with("OR IGNORE"), role_rows)
            if expert_rows:
                session.execute(insert(Expert).prefix_with("OR REPLACE"), expert_rows)
            if movie_expert_rows:
                session.execute(insert(MovieExpert).prefix_with("OR IGNORE"), movie_expert_rows)

            session.commit()

            processed = batch_idx * batch_size
            if limit:
                processed = min(processed, limit)
            print(f"Committed movie batch {batch_idx} (movies processed: {processed})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI args and orchestrate the full load pipeline."""

    parser = argparse.ArgumentParser(description="Load movie and person JSON dumps into SQLite.")
    parser.add_argument("--db-path", type=Path, default=Path("db/movie.db"), help="Target SQLite file path")
    parser.add_argument(
        "--movie-json", type=Path, default=Path("db/json/movie_info.json"), help="Path to movie_info.json"
    )
    parser.add_argument(
        "--people-json", type=Path, default=Path("db/json/people_info.json"), help="Path to people_info.json"
    )
    parser.add_argument("--batch-size", type=int, default=1000, help="Number of items per commit batch")
    parser.add_argument("--limit", type=int, default=None, help="Optional number of movies to load for smoke testing")
    parser.add_argument(
        "--people-limit", type=int, default=None, help="Optional number of people to load for smoke testing"
    )
    parser.add_argument("--no-stream", action="store_true", help="Force json.load even if ijson is installed")

    args = parser.parse_args()

    db_path: Path = args.db_path
    movie_path: Path = args.movie_json
    people_path: Path = args.people_json
    batch_size = max(1, args.batch_size)

    # Always start fresh: remove existing DB file and recreate schema so loads are idempotent.
    if db_path.exists():
        db_path.unlink()

    engine = _make_engine(db_path)
    reset_db(engine)
    engine.dispose()

    if people_path.exists():
        load_people_into_db(people_path=people_path, db_path=db_path, batch_size=batch_size, limit=args.people_limit)
    else:
        print(f"People file not found at {people_path}, skipping People load")

    load_movies_into_db(
        movie_path=movie_path,
        db_path=db_path,
        batch_size=batch_size,
        limit=args.limit,
        force_no_stream=args.no_stream,
    )

    print(f"Finished loading movies into {db_path}")


if __name__ == "__main__":
    main()
