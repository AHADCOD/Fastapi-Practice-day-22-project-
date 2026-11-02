from core.exceptions import PublisherNotFoundError
from sqlalchemy.orm import Session
from models.publisher import Publisher

def create_publisher_service(publisher: dict, db: Session):
    db_publisher = Publisher(**publisher)
    db.add(db_publisher)
    db.commit()
    db.refresh(db_publisher)
    return db_publisher

def get_publisher_service(publisher_id: int, db: Session):
    publisher = db.get(Publisher, publisher_id)
    if not publisher:
        raise PublisherNotFoundError(message="Publisher not found.")
    return publisher