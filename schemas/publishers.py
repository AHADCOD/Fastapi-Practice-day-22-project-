from pydantic import BaseModel, Field, ConfigDict


class PublisherBase(BaseModel):
    name: str = Field(..., description="The name of the publisher", min_length=1)
    country: str = Field(..., description="The country of the publisher", min_length=1)

class PublisherIn(PublisherBase):
    pass

class PublisherOut(PublisherBase):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="The unique identifier of the publisher", ge=1)