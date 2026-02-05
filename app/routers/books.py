from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from app.database import get_db
from app.models import Book
from app.schemas import BookCreate, BookResponse, BookStatus, BorrowRequest

router = APIRouter(prefix="/books", tags=["books"])


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    existing = db.get(Book, payload.serial_number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with serial_number '{payload.serial_number}' already exists.",
        )
    book = Book(
        serial_number=payload.serial_number,
        title=payload.title,
        author=payload.author,
        status=BookStatus.AVAILABLE.value,
    )
    db.add(book)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with serial_number '{payload.serial_number}' already exists.",
        ) from None
    except DBAPIError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {e.orig!s}",
        ) from None
    db.refresh(book)
    return book


@router.get("/", response_model=list[BookResponse])
def list_books(
    book_status: BookStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(Book)
    if book_status is not None:
        query = query.filter(Book.status == book_status.value)
    return query.order_by(Book.serial_number).all()


@router.delete("/{serial_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(serial_number: str, db: Session = Depends(get_db)):
    book = db.get(Book, serial_number)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book '{serial_number}' not found.",
        )
    db.delete(book)
    db.commit()


@router.patch("/{serial_number}/borrow", response_model=BookResponse)
def borrow_book(
    serial_number: str,
    payload: BorrowRequest,
    db: Session = Depends(get_db),
):
    book = (
        db.query(Book).with_for_update().filter_by(serial_number=serial_number).first()
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book '{serial_number}' not found.",
        )
    if book.status == BookStatus.BORROWED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book '{serial_number}' is already borrowed.",
        )
    book.status = BookStatus.BORROWED.value
    book.borrowed_at = datetime.now(UTC)
    book.borrower_card_number = payload.borrower_card_number
    db.commit()
    db.refresh(book)
    return book


@router.patch("/{serial_number}/return", response_model=BookResponse)
def return_book(serial_number: str, db: Session = Depends(get_db)):
    book = (
        db.query(Book).with_for_update().filter_by(serial_number=serial_number).first()
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book '{serial_number}' not found.",
        )
    if book.status == BookStatus.AVAILABLE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book '{serial_number}' is not currently borrowed.",
        )
    book.status = BookStatus.AVAILABLE.value
    book.borrowed_at = None
    book.borrower_card_number = None
    db.commit()
    db.refresh(book)
    return book
