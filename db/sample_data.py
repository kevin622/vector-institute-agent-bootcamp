import random
from typing import List, Dict


def generate_users(n: int) -> List[Dict]:
    random.seed(42)
    users: List[Dict] = []
    for i in range(n):
        name = f"사용자{i+1:02d}"
        email = f"user{i+1:02d}@example.com"
        age = random.randint(22, 55)
        users.append({"name": name, "email": email, "age": age})
    return users


def generate_projects(n: int) -> List[Dict]:
    random.seed(123)
    projects: List[Dict] = []
    for i in range(n):
        title = f"프로젝트 {i+1:02d}"
        description = f"자동 생성된 설명 #{i+1}"
        budget = round(random.uniform(5000.0, 15000.0), 2)
        projects.append({"title": title, "description": description, "budget": budget})
    return projects
