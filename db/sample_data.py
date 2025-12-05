import random
from typing import List, Dict


# ----- Generators for realistic B2B AI company -----

DEPARTMENTS = [
    {"name": "Research", "location": "Toronto"},
    {"name": "Engineering", "location": "Toronto"},
    {"name": "Product", "location": "Toronto"},
    {"name": "Sales", "location": "New York"},
    {"name": "Customer Success", "location": "Chicago"},
]

PRODUCT_CATALOG = [
    {
        "name": "VisionGuard AI",
        "category": "Computer Vision",
        "price": 120000,
        "billing": "annual",
    },
    {
        "name": "TextSense NLP",
        "category": "NLP",
        "price": 95000,
        "billing": "annual",
    },
    {
        "name": "ForecastPro",
        "category": "Time Series",
        "price": 80000,
        "billing": "annual",
    },
    {
        "name": "GraphInsight",
        "category": "Graph ML",
        "price": 110000,
        "billing": "annual",
    },
]


def generate_departments(n: int) -> List[Dict]:
    # Repeat/trim from catalog to reach n (10-30)
    items = []
    idx = 0
    while len(items) < n:
        base = DEPARTMENTS[idx % len(DEPARTMENTS)].copy()
        suffix = (idx // len(DEPARTMENTS)) + 1
        base["name"] = base["name"] if suffix == 1 else f"{base['name']} {suffix}"
        items.append(base)
        idx += 1
    return items[:n]


def generate_employees(n: int, departments: List[Dict]) -> List[Dict]:
    random.seed(7)
    first_names = [
        "Minji",
        "Jiwon",
        "Hyun",
        "Sujin",
        "Hana",
        "Jisoo",
        "Taeyang",
        "Joon",
        "Mingyu",
        "Eunwoo",
        "Seojin",
        "Hyejin",
        "Donghyun",
        "Yuna",
        "Sangmin",
    ]
    last_names = ["Park", "Kim", "Lee", "Choi", "Jung", "Kang", "Yoon", "Han"]
    titles = [
        "Research Scientist",
        "ML Engineer",
        "Data Engineer",
        "Product Manager",
        "Sales Manager",
        "Account Executive",
        "Solutions Architect",
        "Customer Success Manager",
    ]

    employees: List[Dict] = []
    used_emails: set[str] = set()
    for i in range(n):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        base_email = f"{name.lower().replace(' ', '.')}@vectorai.com"
        email = base_email
        suffix = 2
        while email in used_emails:
            email = base_email.replace("@", f"{suffix}@")
            suffix += 1
        used_emails.add(email)
        dept = random.choice(departments)
        title = random.choice(titles)
        employees.append(
            {
                "name": name,
                "email": email,
                "title": title,
                "department_name": dept["name"],
            }
        )
    return employees


def generate_products(n: int) -> List[Dict]:
    items = []
    idx = 0
    while len(items) < n:
        base = PRODUCT_CATALOG[idx % len(PRODUCT_CATALOG)].copy()
        suffix = (idx // len(PRODUCT_CATALOG)) + 1
        base["name"] = base["name"] if suffix == 1 else f"{base['name']} v{suffix}"
        # Add small price variance
        base["price"] = int(base["price"] * random.uniform(0.9, 1.15))
        items.append(base)
        idx += 1
    return items[:n]


def generate_clients(n: int) -> List[Dict]:
    random.seed(11)
    industries = [
        "Retail",
        "Finance",
        "Healthcare",
        "Manufacturing",
        "Technology",
        "Energy",
    ]
    cities = ["New York", "Chicago", "San Francisco", "Toronto", "Boston", "Seattle"]
    clients: List[Dict] = []
    for i in range(n):
        name = f"Acme Corp {i+1:02d}"
        clients.append(
            {
                "name": name,
                "industry": random.choice(industries),
                "city": random.choice(cities),
            }
        )
    return clients


def generate_contracts(n: int, clients: List[Dict], products: List[Dict], employees: List[Dict]) -> List[Dict]:
    random.seed(13)
    terms = ["12 months", "24 months", "6 months"]
    statuses = ["active", "pending", "closed"]
    contracts: List[Dict] = []
    for i in range(n):
        client = random.choice(clients)
        product = random.choice(products)
        rep = random.choice([e for e in employees if "Sales" in e["title"] or "Account" in e["title"]])
        amount = int(product["price"] * random.uniform(0.8, 1.3))
        contracts.append(
            {
                "client_name": client["name"],
                "product_name": product["name"],
                "sales_rep_email": rep["email"],
                "amount": amount,
                "term": random.choice(terms),
                "status": random.choice(statuses),
            }
        )
    return contracts


def generate_invoices(n: int, contracts: List[Dict]) -> List[Dict]:
    random.seed(17)
    methods = ["wire", "credit_card", "ach"]
    invoices: List[Dict] = []
    for i in range(n):
        contract = random.choice(contracts)
        due = int(contract["amount"] * random.uniform(0.25, 0.5))
        paid = due if random.random() > 0.2 else int(due * random.uniform(0.3, 0.9))
        invoices.append(
            {
                "contract_client_name": contract["client_name"],
                "contract_product_name": contract["product_name"],
                "amount_due": due,
                "amount_paid": paid,
                "method": random.choice(methods),
            }
        )
    return invoices


def generate_projects(n: int, clients: List[Dict], products: List[Dict], employees: List[Dict]) -> List[Dict]:
    random.seed(19)
    phases = ["PoC", "Pilot", "Production"]
    projects: List[Dict] = []
    for i in range(n):
        client = random.choice(clients)
        product = random.choice(products)
        owner = random.choice([e for e in employees if "Engineer" in e["title"] or "Scientist" in e["title"] or "Architect" in e["title"]])
        projects.append(
            {
                "name": f"{product['name']} - {client['name']} Deployment",
                "client_name": client["name"],
                "product_name": product["name"],
                "owner_email": owner["email"],
                "phase": random.choice(phases),
            }
        )
    return projects


def generate_meetings(n: int, clients: List[Dict], employees: List[Dict]) -> List[Dict]:
    random.seed(23)
    topics = [
        "Quarterly Business Review",
        "Technical Architecture",
        "Roadmap Alignment",
        "Renewal Discussion",
        "Pilot Feedback",
    ]
    meetings: List[Dict] = []
    for i in range(n):
        client = random.choice(clients)
        host = random.choice(employees)
        meetings.append(
            {
                "client_name": client["name"],
                "host_email": host["email"],
                "topic": random.choice(topics),
            }
        )
    return meetings


def generate_project_assignments(n: int, projects: List[Dict], employees: List[Dict]) -> List[Dict]:
    """Generate many-to-many project participation with roles."""
    random.seed(29)
    roles = ["Owner", "Tech Lead", "Engineer", "Scientist", "Architect", "CSM"]
    assignments: List[Dict] = []
    # ensure at least one owner per project present in dataset
    owner_emails = {p.get("owner_email") for p in projects if p.get("owner_email")}
    email_to_emp = {e["email"]: e for e in employees}
    for p in projects:
        owner_email = p.get("owner_email")
        if owner_email and owner_email in email_to_emp:
            assignments.append({"project_name": p["name"], "employee_email": owner_email, "role": "Owner"})
    # add random participants per project (2-6 each)
    for p in projects:
        count = random.randint(2, 6)
        picks = random.sample(employees, k=min(count, len(employees)))
        for e in picks:
            role = random.choice([r for r in roles if r != "Owner"])  # avoid duplicating owner
            assignments.append({"project_name": p["name"], "employee_email": e["email"], "role": role})
    # trim to n if oversized
    return assignments[:n]
