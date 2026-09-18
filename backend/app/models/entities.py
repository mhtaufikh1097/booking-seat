from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (JSON, Date, DateTime, ForeignKey, Index, Integer, String,
                        Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    users: Mapped[list[User]] = relationship(back_populates="role")


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_status", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    role: Mapped[Role] = relationship(back_populates="users")
    employee: Mapped[Optional[Employee]] = relationship(back_populates="user", uselist=False)
    imported_manifests: Mapped[list[Manifest]] = relationship(back_populates="importer")
    system_logs: Mapped[list[SystemLog]] = relationship(back_populates="user")


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    employees: Mapped[list[Employee]] = relationship(back_populates="department")


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (Index("ix_employees_status", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    employee_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"))
    position: Mapped[Optional[str]] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    user: Mapped[Optional[User]] = relationship(back_populates="employee")
    department: Mapped[Optional[Department]] = relationship(back_populates="employees")
    bookings: Mapped[list[EmployeeBooking]] = relationship(back_populates="employee")


class Train(TimestampMixin, Base):
    __tablename__ = "trains"
    __table_args__ = (
        UniqueConstraint("train_number", "travel_date", name="uq_trains_number_date"),
        Index("ix_trains_travel_date_status", "travel_date", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    train_number: Mapped[str] = mapped_column(String(32), nullable=False)
    route_from: Mapped[str] = mapped_column(String(120), nullable=False)
    route_to: Mapped[str] = mapped_column(String(120), nullable=False)
    travel_date: Mapped[date] = mapped_column(Date, nullable=False)
    class_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    carriages: Mapped[list[Carriage]] = relationship(back_populates="train", cascade="all, delete-orphan")
    manifests: Mapped[list[Manifest]] = relationship(back_populates="train")
    bookings: Mapped[list[EmployeeBooking]] = relationship(back_populates="train")


class Carriage(TimestampMixin, Base):
    __tablename__ = "carriages"
    __table_args__ = (UniqueConstraint("train_id", "carriage_number", name="uq_carriages_train_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id", ondelete="CASCADE"), nullable=False)
    carriage_number: Mapped[str] = mapped_column(String(10), nullable=False)
    class_type: Mapped[str] = mapped_column(String(80), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_config: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    train: Mapped[Train] = relationship(back_populates="carriages")
    seats: Mapped[list[Seat]] = relationship(back_populates="carriage", cascade="all, delete-orphan")
    passenger_records: Mapped[list[ManifestPassenger]] = relationship(back_populates="carriage")
    bookings: Mapped[list[EmployeeBooking]] = relationship(back_populates="carriage")


class Seat(TimestampMixin, Base):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("carriage_id", "seat_code", name="uq_seats_carriage_code"),
        Index("ix_seats_carriage_status", "carriage_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    carriage_id: Mapped[int] = mapped_column(ForeignKey("carriages.id", ondelete="CASCADE"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_letter: Mapped[str] = mapped_column(String(5), nullable=False)
    seat_code: Mapped[str] = mapped_column(String(10), nullable=False)
    position_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    carriage: Mapped[Carriage] = relationship(back_populates="seats")
    passenger_records: Mapped[list[ManifestPassenger]] = relationship(back_populates="seat")
    bookings: Mapped[list[EmployeeBooking]] = relationship(back_populates="seat")


class Manifest(TimestampMixin, Base):
    __tablename__ = "manifests"
    __table_args__ = (Index("ix_manifests_train_status", "train_id", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id", ondelete="RESTRICT"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    imported_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    remarks: Mapped[Optional[str]] = mapped_column(Text)

    train: Mapped[Train] = relationship(back_populates="manifests")
    importer: Mapped[User] = relationship(back_populates="imported_manifests")
    passengers: Mapped[list[ManifestPassenger]] = relationship(back_populates="manifest", cascade="all, delete-orphan")


class ManifestPassenger(TimestampMixin, Base):
    __tablename__ = "manifest_passengers"
    __table_args__ = (
        UniqueConstraint("manifest_id", "seat_id", name="uq_manifest_passengers_manifest_seat"),
        Index("ix_manifest_passengers_carriage_seat", "carriage_id", "seat_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manifest_id: Mapped[int] = mapped_column(ForeignKey("manifests.id", ondelete="CASCADE"), nullable=False)
    carriage_id: Mapped[int] = mapped_column(ForeignKey("carriages.id", ondelete="RESTRICT"), nullable=False)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="RESTRICT"), nullable=False)
    passenger_name: Mapped[Optional[str]] = mapped_column(String(120))
    id_number: Mapped[Optional[str]] = mapped_column(String(80))
    ticket_number: Mapped[Optional[str]] = mapped_column(String(80))
    booking_reference: Mapped[Optional[str]] = mapped_column(String(80))

    manifest: Mapped[Manifest] = relationship(back_populates="passengers")
    carriage: Mapped[Carriage] = relationship(back_populates="passenger_records")
    seat: Mapped[Seat] = relationship(back_populates="passenger_records")


class EmployeeBooking(TimestampMixin, Base):
    __tablename__ = "employee_bookings"
    __table_args__ = (
        Index("ix_employee_bookings_train_status", "train_id", "status"),
        Index("ix_employee_bookings_employee_status", "employee_id", "status"),
        UniqueConstraint("train_id", "seat_id", "active_booking_key", name="uq_active_employee_seat"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id", ondelete="RESTRICT"), nullable=False)
    carriage_id: Mapped[int] = mapped_column(ForeignKey("carriages.id", ondelete="RESTRICT"), nullable=False)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False)
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="reserved")
    active_booking_key: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    train: Mapped[Train] = relationship(back_populates="bookings")
    carriage: Mapped[Carriage] = relationship(back_populates="bookings")
    seat: Mapped[Seat] = relationship(back_populates="bookings")
    employee: Mapped[Employee] = relationship(back_populates="bookings")
    history: Mapped[list[BookingHistory]] = relationship(back_populates="booking", cascade="all, delete-orphan")


class BookingHistory(TimestampMixin, Base):
    __tablename__ = "booking_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_booking_id: Mapped[int] = mapped_column(ForeignKey("employee_bookings.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    booking: Mapped[EmployeeBooking] = relationship(back_populates="history")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    table_name: Mapped[Optional[str]] = mapped_column(String(80))
    record_id: Mapped[Optional[int]] = mapped_column(Integer)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user: Mapped[Optional[User]] = relationship(back_populates="system_logs")
