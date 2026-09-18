from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrainStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class CarriageStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class SeatStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TrainCreate(BaseModel):
    train_number: str = Field(min_length=1, max_length=32)
    route_from: str = Field(min_length=1, max_length=120)
    route_to: str = Field(min_length=1, max_length=120)
    travel_date: date
    class_type: str = Field(min_length=1, max_length=80)
    status: TrainStatus = TrainStatus.ACTIVE


class TrainUpdate(BaseModel):
    train_number: str | None = Field(default=None, min_length=1, max_length=32)
    route_from: str | None = Field(default=None, min_length=1, max_length=120)
    route_to: str | None = Field(default=None, min_length=1, max_length=120)
    travel_date: date | None = None
    class_type: str | None = Field(default=None, min_length=1, max_length=80)
    status: TrainStatus | None = None


class TrainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    train_number: str
    route_from: str
    route_to: str
    travel_date: date
    class_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class CarriageCreate(BaseModel):
    carriage_number: str = Field(min_length=1, max_length=10)
    class_type: str = Field(min_length=1, max_length=80)
    total_rows: int = Field(ge=1, le=1000)
    seat_config: list[str] = Field(min_length=1, max_length=50)
    status: CarriageStatus = CarriageStatus.ACTIVE

    @field_validator("carriage_number")
    @classmethod
    def normalize_carriage_number(cls, value: str) -> str:
        value = value.strip()
        if not value.isdigit() or int(value) < 1:
            raise ValueError("carriage_number must be a positive numeric value")
        return str(int(value)).zfill(2)

    @field_validator("seat_config")
    @classmethod
    def validate_seat_config(cls, value: list[str]) -> list[str]:
        normalized = [seat.strip().upper() for seat in value]
        if any(not seat or len(seat) > 5 for seat in normalized):
            raise ValueError("seat_config entries must contain 1-5 characters")
        if len(set(normalized)) != len(normalized):
            raise ValueError("seat_config must not contain duplicate values")
        return normalized


class CarriageUpdate(BaseModel):
    carriage_number: str | None = Field(default=None, min_length=1, max_length=10)
    class_type: str | None = Field(default=None, min_length=1, max_length=80)
    total_rows: int | None = Field(default=None, ge=1, le=1000)
    seat_config: list[str] | None = Field(default=None, min_length=1, max_length=50)
    status: CarriageStatus | None = None

    @field_validator("carriage_number")
    @classmethod
    def normalize_carriage_number(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value.isdigit() or int(value) < 1:
            raise ValueError("carriage_number must be a positive numeric value")
        return str(int(value)).zfill(2)

    @field_validator("seat_config")
    @classmethod
    def validate_seat_config(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = [seat.strip().upper() for seat in value]
        if any(not seat or len(seat) > 5 for seat in normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("seat_config must contain unique values of 1-5 characters")
        return normalized


class CarriageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    train_id: int
    carriage_number: str
    class_type: str
    total_rows: int
    seat_config: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class SeatUpdate(BaseModel):
    status: SeatStatus | None = None
    position_order: int | None = Field(default=None, ge=1)


class SeatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    carriage_id: int
    row_number: int
    seat_letter: str
    seat_code: str
    position_order: int
    status: str
    created_at: datetime
    updated_at: datetime


class SeatGenerationResponse(BaseModel):
    carriage_id: int
    generated_count: int
    seats: list[SeatResponse]