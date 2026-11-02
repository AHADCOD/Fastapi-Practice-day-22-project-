from fastapi import FastAPI
from core.exceptions import register_exception_handlers
from routers.book import BookRouter
from routers.member import MemberRouter
from routers.loan import LoanRouter
from routers.publisher import PublisherRouter


app = FastAPI(title="library Management System")

register_exception_handlers(app)
app.include_router(BookRouter)
app.include_router(MemberRouter)
app.include_router(LoanRouter)
app.include_router(PublisherRouter)


@app.get("/")
def root():
    return {"message": "Welcome"}

