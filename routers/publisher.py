from fastapi import APIRouter, status, Depends, Path
from schemas.publishers import PublisherIn, PublisherOut
from core.dependencies import require_admin
from services.publisher_services import create_publisher_service, get_publisher_service
from core.database import get_db
from sqlalchemy.orm import Session

PublisherRouter = APIRouter(prefix="/publisher",tags=["Publisher"])

@PublisherRouter.post("/", status_code=status.HTTP_201_CREATED, response_model=PublisherOut, dependencies=[Depends(require_admin)])
def create_publisher(publisher: PublisherIn, db: Session = Depends(get_db)):
    publisher_data = publisher.model_dump()
    return create_publisher_service(publisher_data, db)

@PublisherRouter.get("/{publisher_id}", response_model=PublisherOut)
def get_publisher(publisher_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    return get_publisher_service(publisher_id, db)
