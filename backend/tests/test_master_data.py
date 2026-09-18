from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models import Base, Role, User


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    with testing_session.begin() as db:
        roles = {name: Role(name=name, description=name) for name in ("Admin", "Operator", "Manager", "Employee")}
        db.add_all(roles.values())
        db.flush()
        for name in roles:
            db.add(User(role_id=roles[name].id, name=name, email=f"{name.lower()}@example.com", password_hash=hash_password(f"{name}Pass123!"), status="active"))

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    previous_secret = settings.jwt_secret_key
    settings.jwt_secret_key = "test-master-data-secret"
    with TestClient(app) as test_client:
        yield test_client
    settings.jwt_secret_key = previous_secret
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def token(client: TestClient, role: str) -> str:
    response = client.post("/api/v1/auth/login", data={"username": f"{role.lower()}@example.com", "password": f"{role}Pass123!"})
    assert response.status_code == 200
    return response.json()["access_token"]


def train_payload(number: str = "G1016") -> dict[str, object]:
    return {"train_number": number, "route_from": "Tegalluar", "route_to": "Halim", "travel_date": "2026-09-17", "class_type": "Premium Economy", "status": "active"}


def test_role_permissions_for_train_management(client: TestClient) -> None:
    admin = {"Authorization": f"Bearer {token(client, 'Admin')}"}
    operator = {"Authorization": f"Bearer {token(client, 'Operator')}"}
    manager = {"Authorization": f"Bearer {token(client, 'Manager')}"}
    employee = {"Authorization": f"Bearer {token(client, 'Employee')}"}

    assert client.post("/api/v1/trains", json=train_payload(), headers=admin).status_code == 201
    assert client.post("/api/v1/trains", json=train_payload("G1017"), headers=operator).status_code == 201
    assert client.get("/api/v1/trains", headers=manager).status_code == 200
    assert client.post("/api/v1/trains", json=train_payload("G1018"), headers=employee).status_code == 403


def test_duplicate_train_and_carriage_are_rejected(client: TestClient) -> None:
    admin = {"Authorization": f"Bearer {token(client, 'Admin')}"}
    train = client.post("/api/v1/trains", json=train_payload(), headers=admin).json()
    assert client.post("/api/v1/trains", json=train_payload(), headers=admin).status_code == 409
    carriage = {"carriage_number": "02", "class_type": "Premium Economy", "total_rows": 2, "seat_config": ["A", "B"]}
    assert client.post(f"/api/v1/trains/{train['id']}/carriages", json=carriage, headers=admin).status_code == 201
    assert client.post(f"/api/v1/trains/{train['id']}/carriages", json=carriage, headers=admin).status_code == 409


def test_seat_generation_uses_configured_layout_and_is_idempotency_guarded(client: TestClient) -> None:
    admin = {"Authorization": f"Bearer {token(client, 'Admin')}"}
    train = client.post("/api/v1/trains", json=train_payload(), headers=admin).json()
    carriage = {"carriage_number": "08", "class_type": "Premium Economy", "total_rows": 3, "seat_config": ["A", "C", "D", "F"]}
    carriage_response = client.post(f"/api/v1/trains/{train['id']}/carriages", json=carriage, headers=admin)
    carriage_id = carriage_response.json()["id"]
    generated = client.post(f"/api/v1/carriages/{carriage_id}/seats/generate", headers=admin)
    assert generated.status_code == 201
    body = generated.json()
    assert body["generated_count"] == 12
    assert [seat["seat_code"] for seat in body["seats"][:4]] == ["1A", "1C", "1D", "1F"]
    assert client.post(f"/api/v1/carriages/{carriage_id}/seats/generate", headers=admin).status_code == 409
    assert len(client.get(f"/api/v1/carriages/{carriage_id}/seats", headers=admin).json()) == 12


def test_manager_can_view_but_cannot_mutate_and_employee_is_denied(client: TestClient) -> None:
    admin = {"Authorization": f"Bearer {token(client, 'Admin')}"}
    manager = {"Authorization": f"Bearer {token(client, 'Manager')}"}
    employee = {"Authorization": f"Bearer {token(client, 'Employee')}"}
    train = client.post("/api/v1/trains", json=train_payload(), headers=admin).json()
    assert client.get(f"/api/v1/trains/{train['id']}", headers=manager).status_code == 200
    assert client.put(f"/api/v1/trains/{train['id']}", json={"route_to": "Padalarang"}, headers=manager).status_code == 403
    assert client.get("/api/v1/trains", headers=employee).status_code == 403
