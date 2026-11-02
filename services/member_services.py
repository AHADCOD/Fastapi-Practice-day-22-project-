from core.exceptions import DuplicateEmailError, MemberNotFoundError
from schemas.members import MembershipType
from core.dependencies import PaginationParams, pagination
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.member import Member

def check_member(member_id: int, db: Session):
    member = db.execute(select(Member).where(Member.id == member_id)).scalars().first()
    if not member:
        raise MemberNotFoundError(message=f"Member with ID {member_id} does not exist.")
    return member

def create_member_service(member: dict, db: Session):
    existing_member = db.execute(select(Member).where(Member.email == member["email"].lower())).scalars().first()
    if existing_member:
        raise DuplicateEmailError(message="Duplicate Email. Member of this email already exits.")

    new_member = Member(name=member["name"], email=member["email"].lower(), membership_type=member["membership_type"])
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

def get_members_service(membership_type: MembershipType | None, pagination_params: PaginationParams, db: Session):
    result = []
    stmt = select(Member)
    if membership_type:
        stmt = stmt.where(Member.membership_type == membership_type.value)
    result = db.execute(stmt).scalars().all()
    return pagination(pagination_params.skip, pagination_params.limit, result)


def get_member_service(member_id: int, db: Session):
    member = check_member(member_id, db)
    return member

def update_member_service(member_id: int, member: dict, db: Session):
    existing_member = check_member(member_id, db)
    stmt = select(Member).where(Member.email == member.get("email", existing_member.email).lower(), Member.id != member_id)
    duplicate_member = db.execute(stmt).scalars().first()
    if duplicate_member:
        raise DuplicateEmailError(message="Duplicate Email. Member of this email already exits.")
    for key, value in member.items():
        if value is not None:
            setattr(existing_member, key, value)
    db.commit()
    db.refresh(existing_member)
    return existing_member
