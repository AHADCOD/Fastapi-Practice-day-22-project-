from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, computed_field
from core.utilities import validate_isbn10_strict, validate_isbn13_strict
from core.exceptions import ISBNValidationError, LibraryError
from enum import Enum
from .publishers import PublisherOut

class Genre(str, Enum):
    FICTION = "fiction"
    NONFICTION = "nonfiction"
    SCI_FI = "sci-fi"
    BIOGRAPHY = "biography"
    FANTASY = "fantasy"
    reference = "reference"



class BookBase(BaseModel):
    title: str = Field(..., description="The title of the book", min_length=1)
    author: str = Field(..., description="The author of the book", min_length=1)
    genre: Genre = Field(..., description="The genre of the book")
    isbn: str = Field(..., description="The ISBN of the book", min_length=1, max_length=13)
    total_copies: int = Field(..., description="The total number of copies of the book", ge=1)
    available_copies: int = Field(..., description="The number of available copies of the book", ge=0)
    publisher_id: int = Field(..., description="The id of publisher of the book", gt=0)
    
    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value):
        if len(value) == 10:
            return validate_isbn10_strict(value)
        elif len(value) == 13:
            return validate_isbn13_strict(value)
        else:
            raise ISBNValidationError(status_code=400, message="ISBN must be either 10 or 13 characters long")

    @model_validator(mode="after")
    def check_available_copies(self):
        if self.available_copies > self.total_copies:
            raise LibraryError(status_code=400, message="Available copies cannot exceed total copies")
        return self

class BookIn(BookBase):
    pass

class BookOut(BookBase):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="The unique identifier of the book", ge=1)
    publisher: PublisherOut = Field(..., description="The publisher of the book")
    @computed_field
    @property
    def is_available(self) -> bool:
        return self.available_copies > 0

class BookUpdate(BaseModel):
    title: str | None = Field(None, description="The title of the book", min_length=1)
    author: str | None = Field(None, description="The author of the book", min_length=1)
    genre: Genre | None = Field(None, description="The genre of the book")
    isbn: str | None = Field(None, description="The ISBN of the book", min_length=1, max_length=13)
    total_copies: int | None = Field(None, description="The total number of copies of the book", ge=1)
    available_copies: int | None = Field(None, description="The number of available copies of the book", ge=0)

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value):
        if len(value) == 10:
            return validate_isbn10_strict(value)
        elif len(value) == 13:
            return validate_isbn13_strict(value)
        else:
            raise ISBNValidationError(status_code=400, message="ISBN must be either 10 or 13 characters long")

    
