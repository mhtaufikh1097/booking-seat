from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Role, User

ROLE_DESCRIPTIONS = {
    "Admin": "Full system access",
    "Operator": "Train, carriage, manifest, seat configuration, and booking access",
    "Manager": "Dashboard, trains, manifests, bookings, and reports access",
    "Employee": "Available trains, seat availability, and own booking access",
}


def seed_roles_and_admin() -> None:
    if not settings.seed_admin_email or not settings.seed_admin_password:
        raise RuntimeError("SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD must be set in .env")

    with SessionLocal.begin() as db:
        roles = {}
        for role_name, description in ROLE_DESCRIPTIONS.items():
            role = db.scalar(select(Role).where(Role.name == role_name))
            if role is None:
                role = Role(name=role_name, description=description)
                db.add(role)
                db.flush()
            roles[role_name] = role

        email = settings.seed_admin_email.lower().strip()
        admin = db.scalar(select(User).where(User.email == email))
        if admin is None:
            db.add(
                User(
                    role_id=roles["Admin"].id,
                    name=settings.seed_admin_name,
                    email=email,
                    password_hash=hash_password(settings.seed_admin_password),
                    status="active",
                )
            )
            print(f"Created development admin: {email}")
        else:
            print(f"Admin already exists: {email}")

        print(f"Roles available: {', '.join(ROLE_DESCRIPTIONS)}")


if __name__ == "__main__":
    seed_roles_and_admin()