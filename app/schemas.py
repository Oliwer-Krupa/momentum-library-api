from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class BookStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    BORROWED = "BORROWED"


class BookCreate(BaseModel):
    serial_number: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        examples=["000001"],
    )
    title: str = Field(..., min_length=1, max_length=300)
    author: str = Field(..., min_length=1, max_length=200)


class BorrowRequest(BaseModel):
    borrower_card_number: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        examples=["100001"],
    )


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    serial_number: str
    title: str
    author: str
    status: BookStatus
    borrowed_at: datetime | None
    borrower_card_number: str | None
