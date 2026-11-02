from pydantic import BaseModel, Field, ConfigDict, EmailStr
from enum import Enum

class MembershipType(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"

class MemberBase(BaseModel):
    name: str = Field(..., description="The name of the member", min_length=1)
    email: EmailStr = Field(..., description="The email of the member", min_length=1)
    membership_type: MembershipType = Field(..., description="The type of membership")

class MemberIn(MemberBase):
    pass

class MemberOut(MemberBase):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="The unique identifier of the member", ge=1)

class MemberUpdate(BaseModel):
    name: str | None = Field(None, description="The name of the member", min_length=1)
    email: EmailStr | None = Field(None, description="The email of the member", min_length=1)
    membership_type: MembershipType | None = Field(None, description="The type of membership")

