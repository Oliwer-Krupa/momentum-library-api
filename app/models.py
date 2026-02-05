from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Book(Base):
    __tablename__ = "books"

    serial_number: Mapped[str] = mapped_column(String(6), primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="AVAILABLE")
    borrowed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    borrower_card_number: Mapped[str | None] = mapped_column(
        String(6), nullable=True, default=None
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('AVAILABLE', 'BORROWED')",
            name="ck_books_status",
        ),
        CheckConstraint(
            "status != 'AVAILABLE' "
            "OR (borrowed_at IS NULL AND borrower_card_number IS NULL)",
            name="ck_books_available_fields",
        ),
        CheckConstraint(
            "status != 'BORROWED' "
            "OR (borrowed_at IS NOT NULL AND borrower_card_number IS NOT NULL)",
            name="ck_books_borrowed_fields",
        ),
    )
