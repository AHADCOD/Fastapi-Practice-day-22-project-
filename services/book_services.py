from core.exceptions import DuplicateISBNError, BookNotFoundError, BookHasActiveLoansError
from schemas.books import Genre
from core.utilities import validate_isbn10_strict, validate_isbn13_strict
from core.dependencies import PaginationParams, pagination
from sqlalchemy.orm import Session
from models.book import Book
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.loan import Loan

def check_book(book_id: int, db: Session):
    stmt = select(Book).where(Book.id == book_id)
    book = db.execute(stmt).scalars().first()
    if not book:
        raise BookNotFoundError(message="Book not found.")
    return book



def create_book_service(book: dict, db: Session):
    stmt = select(Book).where(Book.isbn == book["isbn"])
    existing_book = db.execute(stmt).scalars().first()
    if existing_book:
        raise DuplicateISBNError(message="A book with this ISBN already exists.")
    new_book = Book(**book)
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


def get_books_service( genre: Genre | None,
    author: str | None,
    available_only: bool | None, pagination_params: PaginationParams, db: Session):
    results = []
    stmt = select(Book).options(selectinload(Book.publisher))
    if genre:
        stmt = stmt.where(Book.genre == genre)
    if author:
        stmt = stmt.where(Book.author == author)
    if available_only:
        stmt = stmt.where(Book.available_copies > 0)
    results = db.execute(stmt).scalars().all()

    return pagination(pagination_params.skip, pagination_params.limit, results)

def get_available_book_service(pagination_params: PaginationParams, db: Session):
    results = []
    stmt = select(Book).options(selectinload(Book.publisher)).where(Book.available_copies > 0)
    results = db.execute(stmt).scalars().all()
    return pagination(pagination_params.skip, pagination_params.limit, results)


def get_book_service(book_id: int, db: Session):
    book = check_book(book_id, db)
    return book

def update_book_service(book_id: int, book_update: dict, db: Session):
    book = check_book(book_id, db)

    for key, value in book_update.items():
        if value is not None:
            setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book

def delete_book_service(book_id: int, db: Session):
    book = check_book(book_id, db)
    stmt = select(Loan).where(Loan.book_id == book_id, Loan.status == "active")
    active_loans = db.execute(stmt).scalars().all()
    if active_loans:
        raise BookHasActiveLoansError(message="Cannot delete book with active loans.")
    db.delete(book)
    db.commit()


