# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------

from sqlalchemy.orm import declarative_base
from sqlalchemy import JSON, Column, Date, Enum, ForeignKey, Integer, String, Text

Base = declarative_base()


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
