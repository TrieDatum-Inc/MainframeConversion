from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.routers import accounts, auth, bills, cards, customers, reports, transactions, users
from app.seed import seed_database


@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="CardDemo API",
    description="FastAPI backend for the CardDemo credit card management system, "
    "converted from mainframe COBOL/CICS/VSAM/DB2.",
    version="1.0.0",
    lifespan=lifespan,
)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(customers.router)
app.include_router(cards.router)
app.include_router(transactions.router)
app.include_router(bills.router)
app.include_router(users.router)
app.include_router(reports.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
