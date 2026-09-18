"""Create initial booking seat database schema.

Revision ID: 20260917_0001
Revises:
Create Date: 2026-09-17
"""

from alembic import op
import sqlalchemy as sa

revision = "20260917_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("name", name="uq_departments_name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("last_login_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_users_role_id_roles", ondelete="RESTRICT"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_status", "users", ["status"])
    op.create_table(
        "trains",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("train_number", sa.String(length=32), nullable=False),
        sa.Column("route_from", sa.String(length=120), nullable=False),
        sa.Column("route_to", sa.String(length=120), nullable=False),
        sa.Column("travel_date", sa.Date(), nullable=False),
        sa.Column("class_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_trains_travel_date_status", "trains", ["travel_date", "status"])
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer()),
        sa.Column("employee_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("department_id", sa.Integer()),
        sa.Column("position", sa.String(length=120)),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_employees_user_id_users", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], name="fk_employees_department_id_departments", ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", name="uq_employees_user_id"),
        sa.UniqueConstraint("employee_code", name="uq_employees_employee_code"),
    )
    op.create_index("ix_employees_status", "employees", ["status"])
    op.create_table(
        "carriages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("train_id", sa.Integer(), nullable=False),
        sa.Column("carriage_number", sa.String(length=10), nullable=False),
        sa.Column("class_type", sa.String(length=80), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("seat_config", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["train_id"], ["trains.id"], name="fk_carriages_train_id_trains", ondelete="CASCADE"),
        sa.UniqueConstraint("train_id", "carriage_number", name="uq_carriages_train_number"),
    )
    op.create_table(
        "seats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("carriage_id", sa.Integer(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("seat_letter", sa.String(length=5), nullable=False),
        sa.Column("seat_code", sa.String(length=10), nullable=False),
        sa.Column("position_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["carriage_id"], ["carriages.id"], name="fk_seats_carriage_id_carriages", ondelete="CASCADE"),
        sa.UniqueConstraint("carriage_id", "seat_code", name="uq_seats_carriage_code"),
    )
    op.create_index("ix_seats_carriage_status", "seats", ["carriage_id", "status"])
    op.create_table(
        "manifests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("train_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("imported_by", sa.Integer(), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.Column("total_records", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("remarks", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["train_id"], ["trains.id"], name="fk_manifests_train_id_trains", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["imported_by"], ["users.id"], name="fk_manifests_imported_by_users", ondelete="RESTRICT"),
    )
    op.create_index("ix_manifests_train_status", "manifests", ["train_id", "status"])
    op.create_table(
        "manifest_passengers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("manifest_id", sa.Integer(), nullable=False),
        sa.Column("carriage_id", sa.Integer(), nullable=False),
        sa.Column("seat_id", sa.Integer(), nullable=False),
        sa.Column("passenger_name", sa.String(length=120)),
        sa.Column("id_number", sa.String(length=80)),
        sa.Column("ticket_number", sa.String(length=80)),
        sa.Column("booking_reference", sa.String(length=80)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["manifest_id"], ["manifests.id"], name="fk_manifest_passengers_manifest_id_manifests", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["carriage_id"], ["carriages.id"], name="fk_manifest_passengers_carriage_id_carriages", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], name="fk_manifest_passengers_seat_id_seats", ondelete="RESTRICT"),
        sa.UniqueConstraint("manifest_id", "seat_id", name="uq_manifest_passengers_manifest_seat"),
    )
    op.create_index("ix_manifest_passengers_carriage_seat", "manifest_passengers", ["carriage_id", "seat_id"])
    op.create_table(
        "employee_bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("train_id", sa.Integer(), nullable=False),
        sa.Column("carriage_id", sa.Integer(), nullable=False),
        sa.Column("seat_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("active_booking_key", sa.String(length=80)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["train_id"], ["trains.id"], name="fk_employee_bookings_train_id_trains", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["carriage_id"], ["carriages.id"], name="fk_employee_bookings_carriage_id_carriages", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], name="fk_employee_bookings_seat_id_seats", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], name="fk_employee_bookings_employee_id_employees", ondelete="RESTRICT"),
        sa.UniqueConstraint("train_id", "seat_id", "active_booking_key", name="uq_active_employee_seat"),
    )
    op.create_index("ix_employee_bookings_train_status", "employee_bookings", ["train_id", "status"])
    op.create_index("ix_employee_bookings_employee_status", "employee_bookings", ["employee_id", "status"])
    op.create_table(
        "booking_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_booking_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["employee_booking_id"], ["employee_bookings.id"], name="fk_booking_history_employee_booking_id_employee_bookings", ondelete="CASCADE"),
    )
    op.create_table(
        "system_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer()),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("table_name", sa.String(length=80)),
        sa.Column("record_id", sa.Integer()),
        sa.Column("ip_address", sa.String(length=45)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_system_logs_user_id_users", ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("system_logs")
    op.drop_table("booking_history")
    op.drop_index("ix_employee_bookings_employee_status", table_name="employee_bookings")
    op.drop_index("ix_employee_bookings_train_status", table_name="employee_bookings")
    op.drop_table("employee_bookings")
    op.drop_index("ix_manifest_passengers_carriage_seat", table_name="manifest_passengers")
    op.drop_table("manifest_passengers")
    op.drop_index("ix_manifests_train_status", table_name="manifests")
    op.drop_table("manifests")
    op.drop_index("ix_seats_carriage_status", table_name="seats")
    op.drop_table("seats")
    op.drop_table("carriages")
    op.drop_index("ix_employees_status", table_name="employees")
    op.drop_table("employees")
    op.drop_index("ix_trains_travel_date_status", table_name="trains")
    op.drop_table("trains")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_table("users")
    op.drop_table("departments")
    op.drop_table("roles")
