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
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
import random

try:
    from db.sample_data import (
        generate_departments,
        generate_employees,
        generate_products,
        generate_clients,
        generate_contracts,
        generate_invoices,
        generate_projects,
        generate_meetings,
        generate_project_assignments,
    )
except Exception:
    from sample_data import (  # type: ignore
        generate_departments,
        generate_employees,
        generate_products,
        generate_clients,
        generate_contracts,
        generate_invoices,
        generate_projects,
        generate_meetings,
        generate_project_assignments,
    )

DB_PATH = Path(__file__).parent / "data.db"
Base = declarative_base()
_ENGINE = None
SessionLocal = None


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


# ----- Tables (<= 10) -----

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    location = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False)

    department = relationship("Department", back_populates="employees")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)
    price = Column(Integer, nullable=False)  # annual price in USD
    billing = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    industry = Column(String, nullable=False)
    city = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    sales_rep_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    amount = Column(Integer, nullable=False)
    term = Column(String, nullable=False)  # e.g., "12 months"
    status = Column(String, nullable=False)  # active, pending, closed
    created_at = Column(DateTime(timezone=True), nullable=False)

    client = relationship("Client")
    product = relationship("Product")
    sales_rep = relationship("Employee")


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    amount_due = Column(Integer, nullable=False)
    amount_paid = Column(Integer, nullable=False)
    method = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    contract = relationship("Contract")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    phase = Column(String, nullable=False)  # PoC, Pilot, Production
    created_at = Column(DateTime(timezone=True), nullable=False)

    client = relationship("Client")
    product = relationship("Product")
    owner = relationship("Employee")


class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    host_employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"))
    topic = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    client = relationship("Client")
    host = relationship("Employee")


class ProjectAssignment(Base):
    __tablename__ = "project_assignments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    project = relationship("Project")
    employee = relationship("Employee")


# Defaults: keep each table between 10 and 30 rows
DEFAULT_DEPARTMENTS = 10
DEFAULT_EMPLOYEES = 30
DEFAULT_PRODUCTS = 12
DEFAULT_CLIENTS = 20
DEFAULT_CONTRACTS = 25
DEFAULT_INVOICES = 25
DEFAULT_PROJECTS = 20
DEFAULT_MEETINGS = 20
DEFAULT_ASSIGNMENTS = 60


def reset_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    engine = _get_engine()
    Base.metadata.create_all(engine)


def _index_by_name(items, key):
    return {x[key]: x for x in items}


def insert_data_into_db(
    departments_count: int = DEFAULT_DEPARTMENTS,
    employees_count: int = DEFAULT_EMPLOYEES,
    products_count: int = DEFAULT_PRODUCTS,
    clients_count: int = DEFAULT_CLIENTS,
    contracts_count: int = DEFAULT_CONTRACTS,
    invoices_count: int = DEFAULT_INVOICES,
    projects_count: int = DEFAULT_PROJECTS,
    meetings_count: int = DEFAULT_MEETINGS,
    assignments_count: int = DEFAULT_ASSIGNMENTS,
) -> None:
    random.seed(42)
    now = datetime.now(timezone.utc)
    with get_session() as session:
        # Departments
        dept_data = generate_departments(departments_count)
        dept_objs: dict[str, Department] = {}
        for d in dept_data:
            obj = Department(name=d["name"], location=d["location"], created_at=now)
            session.add(obj)
            dept_objs[d["name"]] = obj
        session.flush()

        # Employees
        emp_data = generate_employees(employees_count, dept_data)
        emp_objs: dict[str, Employee] = {}
        for e in emp_data:
            dep = dept_objs.get(e["department_name"])  # type: ignore
            obj = Employee(
                name=e["name"],
                email=e["email"],
                title=e["title"],
                department_id=dep.id if dep else None,
                created_at=now,
            )
            session.add(obj)
            emp_objs[e["email"]] = obj
        session.flush()

        # Products
        prod_data = generate_products(products_count)
        prod_objs: dict[str, Product] = {}
        for p in prod_data:
            obj = Product(
                name=p["name"],
                category=p["category"],
                price=p["price"],
                billing=p["billing"],
                created_at=now,
            )
            session.add(obj)
            prod_objs[p["name"]] = obj
        session.flush()

        # Clients
        client_data = generate_clients(clients_count)
        client_objs: dict[str, Client] = {}
        for c in client_data:
            obj = Client(
                name=c["name"],
                industry=c["industry"],
                city=c["city"],
                created_at=now,
            )
            session.add(obj)
            client_objs[c["name"]] = obj
        session.flush()

        # Contracts
        contract_data = generate_contracts(contracts_count, client_data, prod_data, emp_data)
        contract_objs: list[Contract] = []
        for ct in contract_data:
            obj = Contract(
                client_id=client_objs[ct["client_name"]].id,
                product_id=prod_objs[ct["product_name"]].id,
                sales_rep_id=emp_objs.get(ct["sales_rep_email"]).id if emp_objs.get(ct["sales_rep_email"]) else None,
                amount=ct["amount"],
                term=ct["term"],
                status=ct["status"],
                created_at=now,
            )
            session.add(obj)
            contract_objs.append(obj)
        session.flush()

        # Invoices
        invoice_data = generate_invoices(invoices_count, contract_data)
        for inv in invoice_data:
            # find matching contract by client+product
            match = next(
                (c for c in contract_objs if c.client.name == inv["contract_client_name"] and c.product.name == inv["contract_product_name"]),
                None,
            )
            if match is None:
                continue
            obj = Invoice(
                contract_id=match.id,
                amount_due=inv["amount_due"],
                amount_paid=inv["amount_paid"],
                method=inv["method"],
                created_at=now,
            )
            session.add(obj)
        session.flush()

        # Projects
        proj_data = generate_projects(projects_count, client_data, prod_data, emp_data)
        for pr in proj_data:
            obj = Project(
                name=pr["name"],
                client_id=client_objs[pr["client_name"]].id,
                product_id=prod_objs[pr["product_name"]].id,
                owner_id=emp_objs.get(pr["owner_email"]).id if emp_objs.get(pr["owner_email"]) else None,
                phase=pr["phase"],
                created_at=now,
            )
            session.add(obj)
        session.flush()

        # Meetings
        mtg_data = generate_meetings(meetings_count, client_data, emp_data)
        for m in mtg_data:
            obj = Meeting(
                client_id=client_objs[m["client_name"]].id,
                host_employee_id=emp_objs.get(m["host_email"]).id if emp_objs.get(m["host_email"]) else None,
                topic=m["topic"],
                created_at=now,
            )
            session.add(obj)

        session.flush()

        # Project Assignments (many-to-many participation)
        # build lightweight dicts for generator
        proj_light = [
            {
                "name": p.name,
                "owner_email": next((e for e_email, e in emp_objs.items() if e.id == p.owner_id), None) and
                next((email for email, e in emp_objs.items() if e.id == p.owner_id), None),
            }
            for p in session.query(Project).all()
        ]
        emp_light = [
            {"email": email}
            for email in emp_objs.keys()
        ]
        assign_data = generate_project_assignments(assignments_count, proj_light, emp_light)
        name_to_project = {p.name: p for p in session.query(Project).all()}
        for a in assign_data:
            proj = name_to_project.get(a["project_name"])  # type: ignore
            emp = emp_objs.get(a["employee_email"])  # type: ignore
            if not proj or not emp:
                continue
            obj = ProjectAssignment(
                project_id=proj.id,
                employee_id=emp.id,
                role=a["role"],
                created_at=now,
            )
            session.add(obj)

        session.commit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reset and seed SQLite DB with realistic B2B AI company data.")
    parser.add_argument("--departments", type=int, default=DEFAULT_DEPARTMENTS)
    parser.add_argument("--employees", type=int, default=DEFAULT_EMPLOYEES)
    parser.add_argument("--products", type=int, default=DEFAULT_PRODUCTS)
    parser.add_argument("--clients", type=int, default=DEFAULT_CLIENTS)
    parser.add_argument("--contracts", type=int, default=DEFAULT_CONTRACTS)
    parser.add_argument("--invoices", type=int, default=DEFAULT_INVOICES)
    parser.add_argument("--projects", type=int, default=DEFAULT_PROJECTS)
    parser.add_argument("--meetings", type=int, default=DEFAULT_MEETINGS)
    parser.add_argument("--assignments", type=int, default=DEFAULT_ASSIGNMENTS)
    args = parser.parse_args()

    reset_db()
    insert_data_into_db(
        departments_count=args.departments,
        employees_count=args.employees,
        products_count=args.products,
        clients_count=args.clients,
        contracts_count=args.contracts,
        invoices_count=args.invoices,
        projects_count=args.projects,
        meetings_count=args.meetings,
        assignments_count=args.assignments,
    )
    total_tables = 9
    print(
        f"Seeded DB at {DB_PATH} with realistic data across {total_tables} tables."
    )
