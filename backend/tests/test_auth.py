from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models import Base, Role, User
from app.core.config import settings


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    with TestingSession.begin() as db:
        admin_role = Role(name="Admin", description="Full system access")
        employee_role = Role(name="Employee", description="Employee access")
        db.add_all([admin_role, employee_role])
        db.flush()
        db.add_all([
            User(role_id=admin_role.id, name="Admin", email="admin@example.com", password_hash=hash_password("AdminPass123!"), status="active"),
            User(role_id=employee_role.id, name="Employee", email="employee@example.com", password_hash=hash_password("EmployeePass123!"), status="active"),
        ])

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    original_secret = settings.jwt_secret_key
    settings.jwt_secret_key = "test-secret-key"
    with TestClient(app) as test_client:
        yield test_client
    settings.jwt_secret_key = original_secret
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_valid_login_and_current_user(client: TestClient) -> None:
    token = login(client, "admin@example.com", "AdminPass123!")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"
    assert response.json()["role"]["name"] == "Admin"


def test_invalid_login_is_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", data={"username": "admin@example.com", "password": "wrong"})
    assert response.status_code == 401


def test_protected_endpoint_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_role_authorization(client: TestClient) -> None:
    employee_token = login(client, "employee@example.com", "EmployeePass123!")
    admin_token = login(client, "admin@example.com", "AdminPass123!")

    employee_response = client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {employee_token}"})
    admin_response = client.get("/api/v1/auth/admin-check", headers={"Authorization": f"Bearer {admin_token}"})

    assert employee_response.status_code == 403
    assert admin_response.status_code == 200