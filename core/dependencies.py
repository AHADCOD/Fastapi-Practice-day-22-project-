from fastapi import Header, HTTPException, Query
from typing import Annotated



def require_admin(X_API_Key: str = Header(...)):
    """Dependency to require an admin API key for certain endpoints."""
    if X_API_Key == None:
        raise HTTPException(status_code=400, detail="X-API-Key header missing.")
    if X_API_Key != "isdunyakapapa":
        raise HTTPException(status_code=403, detail="Admin privileges required.")


class PaginationParams:
    """Dependency to handle pagination parameters."""
    def __init__(self, skip: int , limit: int|None):
        self.skip = skip
        self.limit = limit


def get_pagination_params(skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0, limit: Annotated[int | None, Query(ge=0, description="Maximum number of items to return")] = 10):
    """Dependency to get pagination parameters."""
    return PaginationParams(skip,limit)

def pagination(skip: int, limit: int | None, data: list):
    """Function to paginate a list of data."""
    if limit is None:
        return data[skip:]
    return data[skip: skip + limit]
