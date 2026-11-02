from fastapi.responses import JSONResponse
from fastapi import Request, status

class LibraryError(Exception):
    """Base class for library-related exceptions."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class ISBNValidationError(LibraryError):
    """Exception raised for invalid ISBN formats."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code, message)

class DuplicateISBNError(LibraryError):
    """Exception raised for duplicate ISBN entries."""
    def __init__(self, message: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code, message)

class DuplicateEmailError(LibraryError):
    """Exception raised for duplicate Email entries."""
    def __init__(self, message: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code, message)

class BookNotFoundError(LibraryError):
    """Exception raised when a book is not found."""
    def __init__(self, message: str, status_code: int = status.HTTP_404_NOT_FOUND):
        super().__init__(status_code, message)

class MemberNotFoundError(LibraryError):
    """Exception raised when a member is not found."""
    def __init__(self, message: str, status_code: int = status.HTTP_404_NOT_FOUND):
        super().__init__(status_code, message)

class BookUnavailableError(LibraryError):
    """Exception raised when a book is unavailable."""
    def __init__(self, message: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code, message)

class LoanNotFoundError(LibraryError):
    """Exception raised when a loan is not found."""
    def __init__(self, message: str, status_code: int = status.HTTP_404_NOT_FOUND):
        super().__init__(status_code, message)

class DuplicateLoanError(LibraryError):
    """Exception raised when a duplicate loan is attempted."""
    def __init__(self, message: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code, message)


class LoanLimitExceededError(LibraryError):
    """Exception raised when a member exceeds the loan limit."""
    def __init__(self, message: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code, message)

class BookHasActiveLoansError(LibraryError):
    """Exception raised when a book has active loans."""
    def __init__(self, message: str, status_code: int = status.HTTP_409_CONFLICT):
        super().__init__(status_code, message)

class PublisherNotFoundError(LibraryError):
    """Exception raised when a publisjer is not found."""
    def __init__(self, message: str, status_code: int = status.HTTP_404_NOT_FOUND):
        super().__init__(status_code, message)

    
def register_exception_handlers(app):
    @app.exception_handler(LibraryError)
    def library_exception_handler(request: Request, exc: LibraryError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": type(exc).__name__,
                    "message": exc.message
                }
                },
            )
