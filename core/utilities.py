from core.exceptions import ISBNValidationError

def validate_isbn10_strict(isbn: str):
    """Validates a 10-digit ISBN string. Rejects 'X' as a check digit."""

    # Ensure it is exactly 10 characters and contains only numbers
    if len(isbn) != 10 or not isbn.isdigit():
        raise ISBNValidationError(message="Invalid ISBN format of 10 digits ISBN.")
    
    total = 0
    for i in range(10):
        val = int(isbn[i])
        total += val * (10 - i)
        
    if(total % 11 == 0):
        return isbn
    else:
        raise ISBNValidationError(message="Invalid ISBN format of 10 digits ISBN.")


def validate_isbn13_strict(isbn: str):
    """Validates a 13-digit ISBN string."""
    # Ensure it is exactly 13 characters and contains only numbers
    if len(isbn) != 13 or not isbn.isdigit():
        raise ISBNValidationError(message="Invalid ISBN format of 13 digits ISBN.")
    
    total = 0
    for i in range(13):
        val = int(isbn[i])
        weight = 1 if i % 2 == 0 else 3
        total += val * weight
        
    if(total % 10 == 0):
            return isbn
    else:
        raise ISBNValidationError(message="Invalid ISBN format of 13 digits ISBN.")
