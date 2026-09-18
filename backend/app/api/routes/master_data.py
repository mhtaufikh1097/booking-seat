from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models import User
from app.schemas.master_data import (
    CarriageCreate,
    CarriageResponse,
    CarriageUpdate,
    SeatGenerationResponse,
    SeatResponse,
    SeatUpdate,
    TrainCreate,
    TrainResponse,
    TrainUpdate,
)
from app.services import master_data

router = APIRouter(tags=["master-data"])
VIEW_ROLES = ("Admin", "Operator", "Manager")
MANAGE_ROLES = ("Admin", "Operator")


@router.get("/trains", response_model=list[TrainResponse])
def list_trains(status_filter: str | None = None, db: Session = Depends(get_db), _: User = Depends(require_role(*VIEW_ROLES))):
    return master_data.list_trains(db, status_filter)


@router.post("/trains", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
def create_train(payload: TrainCreate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role(*MANAGE_ROLES))):
    return master_data.create_train(db, payload, user, request)


@router.get("/trains/{train_id}", response_model=TrainResponse)
def get_train(train_id: int, db: Session = Depends(get_db), _: User = Depends(require_role(*VIEW_ROLES))):
    return master_data.get_train(db, train_id)


@router.put("/trains/{train_id}", response_model=TrainResponse)
def update_train(train_id: int, payload: TrainUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role(*MANAGE_ROLES))):
    return master_data.update_train(db, train_id, payload, user, request)


@router.patch("/trains/{train_id}/status", response_model=TrainResponse)
def update_train_status(train_id: int, payload: TrainUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role(*MANAGE_ROLES))):
    if payload.status is None:
        raise HTTPException(status_code=422, detail="status is required")
    action = "ACTIVATE_TRAIN" if payload.status.value == "active" else "DEACTIVATE_TRAIN"
    return master_data.update_train(db, train_id, TrainUpdate(status=payload.status), user, request, action)


@router.get("/trains/{train_id}/carriages", response_model=list[CarriageResponse])
def list_carriages(train_id: int, db: Session = Depends(get_db), _: User = Depends(require_role(*VIEW_ROLES))):
    return master_data.list_carriages(db, train_id)


@router.post("/trains/{train_id}/carriages", response_model=CarriageResponse, status_code=status.HTTP_201_CREATED)
def create_carriage(train_id: int, payload: CarriageCreate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role(*MANAGE_ROLES))):
    return master_data.create_carriage(db, train_id, payload, user, request)


@router.get("/carriages/{carriage_id}", response_model=CarriageResponse)
def get_carriage(carriage_id: int, db: Session = Depends(get_db), _: User = Depends(require_role(*VIEW_ROLES))):
    return master_data.get_carriage(db, carriage_id)


@router.put("/carriages/{carriage_id}", response_model=CarriageResponse)
def update_carriage(carriage_id: int, payload: CarriageUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role(*MANAGE_ROLES))):
    return master_data.update_carriage(db, carriage_id, payload, user, request)


@router.patch("/carriages/{carriage_id}/status", response_model=CarriageResponse)
def update_carriage_status(carriage_id: int, payload: CarriageUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role(*MANAGE_ROLES))):
    if payload.status is None:
        raise HTTPException(status_code=422, detail="status is required")
    action = "ACTIVATE_CARRIAGE" if payload.status.value == "active" else "DEACTIVATE_CARRIAGE"
    return master_data.update_carriage(db, carriage_id, CarriageUpdate(status=payload.status), user, request, action)


@router.get("/carriages/{carriage_id}/seats", response_model=list[SeatResponse])
def list_seats(carriage_id: int, db: Session = Depends(get_db), _: User = Depends(require_role(*VIEW_ROLES))):
    return master_data.list_seats(db, carriage_id)


@router.post("/carriages/{carriage_id}/seats/generate", response_model=SeatGenerationResponse, status_code=status.HTTP_201_CREATED)
def generate_seats(carriage_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role(*MANAGE_ROLES))):
    seats = master_data.generate_seats(db, carriage_id, user, request)
    return {"carriage_id": carriage_id, "generated_count": len(seats), "seats": seats}


@router.patch("/seats/{seat_id}", response_model=SeatResponse)
def update_seat(seat_id: int, payload: SeatUpdate, request: Request, db: Session = Depends(get_db), user: User = Depends(require_role(*MANAGE_ROLES))):
    return master_data.update_seat(db, seat_id, payload, user, request)
