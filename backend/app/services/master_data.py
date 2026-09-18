from datetime import datetime

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Carriage, Seat, SystemLog, Train, User
from app.schemas.master_data import CarriageCreate, CarriageUpdate, SeatUpdate, TrainCreate, TrainUpdate


def _conflict(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


def _not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


def audit(db: Session, user: User, request: Request, action: str, table_name: str, record_id: int) -> None:
    db.add(SystemLog(
        user_id=user.id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        ip_address=request.client.host if request.client else None,
        created_at=datetime.utcnow(),
    ))


def list_trains(db: Session, status_filter: str | None = None) -> list[Train]:
    statement = select(Train).order_by(Train.travel_date, Train.train_number)
    if status_filter:
        statement = statement.where(Train.status == status_filter)
    return list(db.scalars(statement))


def create_train(db: Session, payload: TrainCreate, user: User, request: Request) -> Train:
    train = Train(**payload.model_dump())
    db.add(train)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise _conflict("A train with this number and travel date already exists") from error
    audit(db, user, request, "CREATE_TRAIN", "trains", train.id)
    db.commit()
    db.refresh(train)
    return train


def update_train(db: Session, train_id: int, payload: TrainUpdate, user: User, request: Request, action: str = "UPDATE_TRAIN") -> Train:
    train = db.get(Train, train_id)
    if train is None:
        raise _not_found("Train")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(train, field, value)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise _conflict("A train with this number and travel date already exists") from error
    audit(db, user, request, action, "trains", train.id)
    db.commit()
    db.refresh(train)
    return train


def get_train(db: Session, train_id: int) -> Train:
    train = db.get(Train, train_id)
    if train is None:
        raise _not_found("Train")
    return train


def list_carriages(db: Session, train_id: int) -> list[Carriage]:
    get_train(db, train_id)
    return list(db.scalars(select(Carriage).where(Carriage.train_id == train_id).order_by(Carriage.carriage_number)))


def create_carriage(db: Session, train_id: int, payload: CarriageCreate, user: User, request: Request) -> Carriage:
    get_train(db, train_id)
    carriage = Carriage(train_id=train_id, **payload.model_dump())
    db.add(carriage)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise _conflict("This carriage number already exists for the train") from error
    audit(db, user, request, "CREATE_CARRIAGE", "carriages", carriage.id)
    db.commit()
    db.refresh(carriage)
    return carriage


def get_carriage(db: Session, carriage_id: int) -> Carriage:
    carriage = db.get(Carriage, carriage_id)
    if carriage is None:
        raise _not_found("Carriage")
    return carriage


def update_carriage(db: Session, carriage_id: int, payload: CarriageUpdate, user: User, request: Request, action: str = "UPDATE_CARRIAGE") -> Carriage:
    carriage = get_carriage(db, carriage_id)
    values = payload.model_dump(exclude_unset=True)
    if any(field in values for field in ("total_rows", "seat_config")) and carriage.seats:
        raise _conflict("Regenerate or remove existing seats before changing carriage seat configuration")
    for field, value in values.items():
        setattr(carriage, field, value)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        raise _conflict("This carriage number already exists for the train") from error
    audit(db, user, request, action, "carriages", carriage.id)
    db.commit()
    db.refresh(carriage)
    return carriage


def list_seats(db: Session, carriage_id: int) -> list[Seat]:
    get_carriage(db, carriage_id)
    return list(db.scalars(select(Seat).where(Seat.carriage_id == carriage_id).order_by(Seat.row_number, Seat.position_order)))


def update_seat(db: Session, seat_id: int, payload: SeatUpdate, user: User, request: Request) -> Seat:
    seat = db.get(Seat, seat_id)
    if seat is None:
        raise _not_found("Seat")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(seat, field, value)
    audit(db, user, request, "UPDATE_SEAT", "seats", seat.id)
    db.commit()
    db.refresh(seat)
    return seat


def generate_seats(db: Session, carriage_id: int, user: User, request: Request) -> list[Seat]:
    carriage = get_carriage(db, carriage_id)
    if carriage.seats:
        raise _conflict("Seats have already been generated for this carriage")
    seats = [
        Seat(
            carriage_id=carriage.id,
            row_number=row_number,
            seat_letter=seat_letter,
            seat_code=f"{row_number}{seat_letter}",
            position_order=position,
            status="active",
        )
        for row_number in range(1, carriage.total_rows + 1)
        for position, seat_letter in enumerate(carriage.seat_config, start=1)
    ]
    db.add_all(seats)
    audit(db, user, request, "GENERATE_SEATS", "carriages", carriage.id)
    db.commit()
    for seat in seats:
        db.refresh(seat)
    return seats