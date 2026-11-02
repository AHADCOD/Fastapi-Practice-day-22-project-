from fastapi import APIRouter, Depends, status, Body, Query, Path
from schemas.loans import LoanOut, ReturnStatus
from services.loan_services import create_loan_service, get_loans_service, get_overdue_loans_service, get_loan_service, return_loan_service
from core.dependencies import require_admin, PaginationParams, get_pagination_params
from core.database import get_db
from sqlalchemy.orm import Session
# from typing import Annotated


LoanRouter = APIRouter(prefix="/loans", tags=["Loan"])

@LoanRouter.post("", response_model=LoanOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_loan(member_id : int = Body(embed=True, gt=0), book_id : int = Body(embed=True, gt=0), db: Session = Depends(get_db)):
    return create_loan_service(member_id, book_id, db)

@LoanRouter.get("/", response_model=list[LoanOut])
def get_loans(
    member_id: int = Query(default=None, gt=0),
    book_id: int = Query(default=None, gt=0),
    loan_status: ReturnStatus | None = Query(default=None), 
    pagination_params: PaginationParams = Depends(get_pagination_params), 
    db: Session = Depends(get_db)):

    return get_loans_service(member_id, book_id, loan_status, pagination_params, db)

@LoanRouter.get("/overdue", response_model=list[LoanOut])
def get_overdue_loans(pagination_params: PaginationParams = Depends(get_pagination_params), db: Session = Depends(get_db)):
    return get_overdue_loans_service(pagination_params, db)

@LoanRouter.get("/{loan_id}", response_model=LoanOut)
def get_loan(loan_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    return get_loan_service(loan_id, db)

@LoanRouter.patch("/{loan_id}/return", response_model=LoanOut, dependencies=[Depends(require_admin)])
def return_loan(loan_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    return return_loan_service(loan_id, db)