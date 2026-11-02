from datetime import datetime, timedelta, UTC
from schemas.loans import ReturnStatus
from schemas.books import BookOut
from schemas.members import MemberOut
from .book_services import check_book
from .member_services import check_member
from core.exceptions import BookUnavailableError, LoanNotFoundError, DuplicateLoanError, LoanLimitExceededError
from core.dependencies import PaginationParams, pagination
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from models.loan import Loan


def check_loan(loan_id: int, db: Session):
    stmt = select(Loan).where(Loan.id == loan_id)
    loan = db.execute(stmt).scalars().first()
    if not loan:
        raise LoanNotFoundError(message="Loan not found.")
    return loan



def create_loan_service(member_id: int, book_id: int, db: Session):
    
    member = check_member(member_id, db)
    book = check_book(book_id, db)

    if book.available_copies <= 0:
        raise BookUnavailableError(message="Book is currently unavailable for loan.")

    stmt = select(Loan).where(Loan.member_id == member_id, Loan.book_id == book_id, Loan.status == ReturnStatus.ACTIVE)
    existing_loan = db.execute(stmt).scalars().first()

    if existing_loan:
        raise DuplicateLoanError(message="This member already has an active loan for this book.")

    stmt = select(Loan).where(Loan.member_id == member_id, Loan.status == ReturnStatus.ACTIVE)
    member_loan_count = len(db.execute(stmt).scalars().all())

    if (member.membership_type == "premium" and member_loan_count >= 10) or (member.membership_type == "basic" and member_loan_count >= 3):
        raise LoanLimitExceededError(message="Member has exceeded the loan limit for their membership type.")

    loan_days = 30 if member.membership_type == "premium" else 14
    due_date = datetime.now(UTC) + timedelta(days=loan_days)

    loan_data = {
        "book_id": book_id,
        "member_id": member_id,
        "loan_date": datetime.now(UTC),
        "due_date": due_date,
        "return_date": None,
        "status": ReturnStatus.ACTIVE
    }

    book.available_copies -= 1

    new_loan = Loan(**loan_data)
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    return new_loan

def get_loans_service(member_id: int | None, book_id: int | None, loan_status: ReturnStatus | None, pagination_params: PaginationParams, db: Session):
    results = []
    stmt = select(Loan).options(joinedload(Loan.book), joinedload(Loan.member)).order_by(Loan.loan_date.desc())
    if member_id is not None:
        stmt = stmt.where(Loan.member_id == member_id)
    if book_id is not None:
        stmt = stmt.where(Loan.book_id == book_id)
    if loan_status is not None:
        stmt = stmt.where(Loan.status == loan_status)
    results = db.execute(stmt).scalars().all()

    return pagination(pagination_params.skip, pagination_params.limit, results)


def get_overdue_loans_service(pagination_params: PaginationParams, db: Session):
    results = []
    stmt = select(Loan).options(joinedload(Loan.book), joinedload(Loan.member)).where(Loan.status == ReturnStatus.ACTIVE, Loan.due_date < datetime.now(UTC))
    results = db.execute(stmt).scalars().all()

    return pagination(pagination_params.skip, pagination_params.limit, results)


def get_loan_service(loan_id: int, db: Session):
    loan = check_loan(loan_id, db)
    return loan

def return_loan_service(loan_id: int, db: Session):
    loan = check_loan(loan_id, db)
    if loan.status == ReturnStatus.RETURNED:
        raise LoanNotFoundError(message="This loan has already been returned.")

    loan.return_date = datetime.now(UTC)
    loan.status = ReturnStatus.RETURNED

    book = check_book(loan.book_id, db)
    book.available_copies += 1

    db.commit()
    db.refresh(loan)
    return loan