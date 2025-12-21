"""SQLite loader for movie and person JSON dumps.

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
python -m db.load_movie_json --reset
python -m db.load_movie_json --db-path db/movie.db --limit 500 --batch-size 2000
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional

from sqlalchemy import JSON, Column, Date, Enum, ForeignKey, Integer, String, Text, create_engine, insert, select
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------


class Movie(Base):
    __tablename__ = "Movies"

    movie_code = Column("movieCode", String, primary_key=True, key="movie_code")
    movie_name = Column("movieNm", String, key="movie_name")
    movie_name_en = Column("movieNmEn", String, key="movie_name_en")
    movie_name_org = Column("movieNmOg", String, key="movie_name_org")
    show_time = Column("showTm", String, key="show_time")
    product_year = Column("prdtYear", String, key="product_year")
    open_date = Column("openDt", Date, key="open_date")
    open_date_raw = Column("openDtRaw", String, key="open_date_raw")
    watch_grade_name = Column("watchGradeNm", String, key="watch_grade_name")
    synopsis = Column("synops", Text, key="synopsis")
    audience_count = Column("audiCnt", Integer, key="audience_count")
    type_name = Column("typeNm", String, key="type_name")
    nations = Column("nations", JSON, key="nations")
    genres = Column("genres", JSON, key="genres")
    companys = Column("companys", JSON, key="companys")
    cine21_cd = Column("cine21Cd", String, key="cine21_cd")
    awards = Column("awardsNm", JSON, key="awards")
    awards_top3 = Column("awards_top3", JSON, key="awards_top3")


class Person(Base):
    __tablename__ = "People"

    person_id = Column("personId", String, primary_key=True, key="person_id")
    person_name = Column("personNm", String, key="person_name")
    person_name_en = Column("personEngNm", String, key="person_name_en")
    origin_name = Column("originNm", String, key="origin_name")
    native_name = Column("nativeNm", String, key="native_name")
    ect_name = Column("ectNm", String, key="ect_name")
    country_name = Column("countryNm", String, key="country_name")
    birth_date = Column("birthDt", Date, key="birth_date")
    birth_date_raw = Column("birthDtRaw", String, key="birth_date_raw")
    death_date = Column("deathDt", Date, key="death_date")
    death_date_raw = Column("deathDtRaw", String, key="death_date_raw")
    job_name = Column("jobNm", String, key="job_name")
    sub_job_name = Column("subJobNm", String, key="sub_job_name")
    sex = Column("sexVal", String, key="sex")
    height = Column("hegtval", String, key="height")
    weight = Column("wgtval", String, key="weight")
    education = Column("education", String, key="education")
    hobby = Column("hobyNm", String, key="hobby")
    remark = Column("remrkNm", String, key="remark")
    company = Column("posCmpnNm", String, key="company")
    official_site = Column("officialSite", String, key="official_site")
    image_url = Column("imgFileURL", String, key="image_url")
    age = Column("age", String, key="age")
    zodiac = Column("zodiac", String, key="zodiac")
    constellation = Column("constellation", String, key="constellation")
    updated_at = Column("updateDt", Date, key="updated_at")
    updated_at_raw = Column("updateDtRaw", String, key="updated_at_raw")
    awards = Column("Awards", JSON, key="awards")
    awards_top3 = Column("Awards_Top3", JSON, key="awards_top3")
    directors_filmography_top5 = Column("Directors_Filmography_Top5", JSON, key="directors_filmography_top5")
    actors_filmography_top5 = Column("Actors_Filmography_Top5", JSON, key="actors_filmography_top5")
    filmography_top5 = Column("Filmography_Top5", JSON, key="filmography_top5")
    filmography = Column("Filmography", JSON, key="filmography")
    rel_person = Column("RelPerson", JSON, key="rel_person")


class MoviePersonRole(Base):
    """Bridge table between movies and people with role-specific extras."""

    __tablename__ = "MoviePeople"

    movie_code = Column(
        "movieCode", String, ForeignKey("Movies.movie_code", ondelete="CASCADE"), primary_key=True, key="movie_code"
    )
    person_id = Column(
        "personId", String, ForeignKey("People.person_id", ondelete="CASCADE"), primary_key=True, key="person_id"
    )
    role_type = Column("roleType", Enum("director", "actor", "staff", name="role_type"), primary_key=True)
    actor_role = Column("actorRole", String)
    actor_classification = Column("actorGb", String)
    staff_role = Column("staffRole", String)


class Expert(Base):
    __tablename__ = "Experts"

    expert_id = Column("expertId", String, primary_key=True, key="expert_id")
    expert_name = Column("expertNm", String, key="expert_name")
    expert_name_en = Column("expertNameEng", String, key="expert_name_en")


class MovieExpert(Base):
    __tablename__ = "MovieExperts"

    movie_code = Column(
        "movieCode", String, ForeignKey("Movies.movie_code", ondelete="CASCADE"), primary_key=True, key="movie_code"
    )
    expert_id = Column(
        "expertId", String, ForeignKey("Experts.expert_id", ondelete="CASCADE"), primary_key=True, key="expert_id"
    )
    expert_point = Column("expertPoint", String, key="expert_point")
    expert_comment = Column("expertComment", String, key="expert_comment")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    return str(value)


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    cleaned = re.sub(r"[^0-9]", "", str(value))
    return int(cleaned) if cleaned else None


def _parse_date(value: Optional[str]) -> tuple[Optional[date], Optional[str]]:
    """Parse dates like '2006년 07월 27일' into date; keep raw for auditing.

    If only a year or year-month is present, we pin missing parts to 1 so the
    field can still be stored as a DATE while preserving the raw string beside
    it.
    """

    raw = _strip(value)
    if not raw:
        return None, None

    numbers = [int(x) for x in re.findall(r"\d+", raw)]
    if not numbers:
        return None, raw

    year = numbers[0]
    month = numbers[1] if len(numbers) > 1 else 1
    day = numbers[2] if len(numbers) > 2 else 1
    try:
        return date(year, month, day), raw
    except ValueError:
        return None, raw


def _json_list(values: Any) -> Optional[List[Any]]:
    if values is None:
        return None
    if isinstance(values, list):
        return values
    return [values]


def chunked(iterable: Iterable[Dict[str, Any]], size: int) -> Generator[List[Dict[str, Any]], None, None]:
    batch: List[Dict[str, Any]] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


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
    birth_date, birth_raw = _parse_date(person.get("birthDt"))
    death_date, death_raw = _parse_date(person.get("deathDt"))
    updated_at, updated_raw = _parse_date(person.get("updateDt"))

    return {
        "person_id": _strip(person.get("personId")),
        "person_name": _strip(person.get("personNm")),
        "person_name_en": _strip(person.get("personEngNm")),
        "origin_name": _strip(person.get("originNm")),
        "native_name": _strip(person.get("nativeNm")),
        "ect_name": _strip(person.get("ectNm")),
        "country_name": _strip(person.get("countryNm")),
        "birth_date": birth_date,
        "birth_date_raw": birth_raw,
        "death_date": death_date,
        "death_date_raw": death_raw,
        "job_name": _strip(person.get("jobNm")),
        "sub_job_name": _strip(person.get("subJobNm")),
        "sex": _strip(person.get("sexVal")),
        "height": _strip(person.get("hegtval")),
        "weight": _strip(person.get("wgtval")),
        "education": _strip(person.get("education")),
        "hobby": _strip(person.get("hobyNm")),
        "remark": _strip(person.get("remrkNm")),
        "company": _strip(person.get("posCmpnNm")),
        "official_site": _strip(person.get("officialSite")),
        "image_url": _strip(person.get("imgFileURL")),
        "age": _strip(person.get("age")),
        "zodiac": _strip(person.get("zodiac")),
        "constellation": _strip(person.get("constellation")),
        "updated_at": updated_at,
        "updated_at_raw": updated_raw,
        "awards": _json_list(person.get("Awards")),
        "awards_top3": _json_list(person.get("Awards_Top3")),
        "directors_filmography_top5": _json_list(person.get("Directors_Filmography_Top5")),
        "actors_filmography_top5": _json_list(person.get("Actors_Filmography_Top5")),
        "filmography_top5": _json_list(person.get("Filmography_Top5")),
        "filmography": _json_list(person.get("Filmography")),
        "rel_person": _json_list(person.get("RelPerson")),
    }


def ensure_person(session, person_stub: Dict[str, Any]) -> None:
    """Upsert minimal person info so FK constraints succeed."""

    person_id = _strip(
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
        "person_name": _strip(
            person_stub.get("personNm")
            or person_stub.get("directorNm")
            or person_stub.get("actorNm")
            or person_stub.get("staffNm")
        ),
        "person_name_en": _strip(
            person_stub.get("personNmEn")
            or person_stub.get("directorNmEn")
            or person_stub.get("actorNmEn")
            or person_stub.get("personEngNm")
        ),
    }
    session.execute(insert(Person).prefix_with("OR IGNORE"), [row])


def convert_movie_record(movie: Dict[str, Any]) -> Dict[str, Any]:
    open_date, open_raw = _parse_date(movie.get("openDt"))

    return {
        "movie": {
            "movie_code": _strip(movie.get("movieCd")),
            "movie_name": _strip(movie.get("movieNm")),
            "movie_name_en": _strip(movie.get("movieNmEn")),
            "movie_name_org": _strip(movie.get("movieNmOg")),
            "show_time": _strip(movie.get("showTm")),
            "product_year": _strip(movie.get("prdtYear")),
            "open_date": open_date,
            "open_date_raw": open_raw,
            "watch_grade_name": _strip(movie.get("watchGradeNm")),
            "synopsis": _strip(movie.get("synops")),
            "audience_count": _to_int(movie.get("audiCnt") or movie.get("acdiCnt")),
            "type_name": _strip(movie.get("typeNm")),
            "nations": _json_list(movie.get("nations")),
            "genres": _json_list(movie.get("genres")),
            "companys": _json_list(movie.get("companys")),
            "cine21_cd": _strip(movie.get("cine21Cd")),
            "awards": _json_list(movie.get("awardsNm")),
            "awards_top3": _json_list(movie.get("awards_top3")),
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
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def load_people_into_db(people_path: Path, db_path: Path, batch_size: int = 1000, limit: Optional[int] = None) -> None:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
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
    engine = create_engine(f"sqlite:///{db_path}", future=True)
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

                # Upsert people referenced by roles so FKs hold.
                for director in payload["directors"]:
                    director_id = _strip(director.get("directorId"))
                    # if not director_id:
                    #     print(f"Skipping director with missing ID in movie {movie_row['movie_name']}")
                    #     continue
                    ensure_person(session, director)
                    role_rows.append(
                        {
                            "movie_code": movie_row["movie_code"],
                            "person_id": director_id,
                            "role_type": "director",
                        }
                    )

                for actor in payload["actors"]:
                    actor_id = _strip(actor.get("actorId"))
                    if not actor_id:
                        continue
                    ensure_person(session, actor)
                    role_rows.append(
                        {
                            "movie_code": movie_row["movie_code"],
                            "person_id": actor_id,
                            "role_type": "actor",
                            "actor_role": _strip(actor.get("actorRole")),
                            "actor_classification": _strip(actor.get("actorGb")),
                        }
                    )

                for staff in payload["staffs"]:
                    staff_id = _strip(staff.get("staffId"))
                    if not staff_id:
                        continue
                    ensure_person(session, staff)
                    role_rows.append(
                        {
                            "movie_code": movie_row["movie_code"],
                            "person_id": staff_id,
                            "role_type": "staff",
                            "staff_role": _strip(staff.get("staffRole")),
                        }
                    )

                for expert in payload["experts"]:
                    expert_id = _strip(expert.get("expertId"))
                    if not expert_id:
                        continue
                    expert_rows.append(
                        {
                            "expert_id": expert_id,
                            "expert_name": _strip(expert.get("expertNm")),
                            "expert_name_en": _strip(expert.get("expertNameEng")),
                        }
                    )
                    movie_expert_rows.append(
                        {
                            "movie_code": movie_row["movie_code"],
                            "expert_id": expert_id,
                            "expert_point": _strip(expert.get("expertPoint")),
                            "expert_comment": _strip(expert.get("expertComment")),
                        }
                    )

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

    engine = create_engine(f"sqlite:///{db_path}", future=True)
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
