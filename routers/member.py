from fastapi import APIRouter, Depends, status, Query, Path
from schemas.members import MemberIn, MemberOut, MembershipType, MemberUpdate
from services.member_services import create_member_service, get_members_service, get_member_service, update_member_service
from core.dependencies import PaginationParams, get_pagination_params
from typing import Annotated
from core.database import get_db
from sqlalchemy.orm import Session

MemberRouter = APIRouter(prefix="/members", tags=["Members"])

@MemberRouter.post("/", status_code=status.HTTP_201_CREATED, response_model=MemberOut)
def create_member(member: MemberIn, db: Session = Depends(get_db)):
    member_dict = member.model_dump()
    return create_member_service(member_dict, db)

@MemberRouter.get("/", response_model=list[MemberOut])
def get_members(membership_type: MembershipType| None = None, pagination: PaginationParams = Depends(get_pagination_params), db: Session = Depends(get_db)):
    return get_members_service(membership_type, pagination, db)

@MemberRouter.get("/{member_id}", response_model=MemberOut)
def get_member(member_id: Annotated[int, Path(description="The ID of the member to retrieve", gt=0)], db: Session = Depends(get_db)):
    return get_member_service(member_id, db)

@MemberRouter.patch("/{member_id}", response_model=MemberOut, response_model_exclude_unset=True)
def update_member(member_id: Annotated[int, Path(description="The ID of the member to update", gt=0)], member: MemberUpdate, db: Session = Depends(get_db)):
    member_dict = member.model_dump(exclude_unset=True)
    return update_member_service(member_id, member_dict, db)