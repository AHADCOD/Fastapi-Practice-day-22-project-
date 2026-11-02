from core.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .publisher import Publisher
    from .loan import Loan

class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    genre: Mapped[str] = mapped_column(String, nullable=False)
    isbn: Mapped[str] = mapped_column(String(13), nullable=False, unique=True)
    total_copies: Mapped[int] = mapped_column(nullable=False)
    available_copies: Mapped[int] = mapped_column(nullable=False)
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"), nullable=False)
    publisher: Mapped["Publisher"] = relationship(back_populates="books")
    loans: Mapped[list["Loan"]] = relationship(back_populates="book", cascade="all, delete-orphan")

