from pydantic import BaseModel, Field,ConfigDict, computed_field
from datetime import datetime, UTC
from enum import Enum
from .books import BookOut
from .members import MemberOut

class ReturnStatus(str, Enum):
    RETURNED = "returned"
    ACTIVE = "active"

class LoanBase(BaseModel):
    book_id: int = Field(..., description="The ID of the book being loaned", ge=1)
    member_id: int = Field(..., description="The ID of the user borrowing the book", ge=1)
    loan_date: datetime = Field(default_factory=lambda: datetime.now(UTC))

class LoanIn(LoanBase):
    pass

class LoanOut(LoanBase):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="The unique identifier for the loan")
    book_id: int = Field(..., description="The ID of the book being loaned", ge=1)
    member_id: int = Field(..., description="The ID of the user borrowing the book", ge=1)
    due_date: datetime |None = Field(None, description="The due date for returning the book")
    return_date: datetime |None = Field(None, description="The date the book was returned")
    status: ReturnStatus
    member: MemberOut = Field(..., description="The member who borrowed the book")
    book: BookOut = Field(..., description="The book that was loaned")

    @computed_field
    @property
    def is_overdue(self) -> bool:
        if self.status != ReturnStatus.ACTIVE or self.due_date is None:
            return False

        due_date = self.due_date
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=UTC)

        return due_date < datetime.now(UTC)





