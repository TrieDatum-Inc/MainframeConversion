from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import (
    auth,
    accounts,
    cards,
    transactions,
    reports,
    bill_payment,
    authorizations,
    users,
    transaction_types,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CardDemo API",
    description=(
        "FastAPI REST API conversion of CardDemo mainframe CICS programs. "
        "Each endpoint maps to a specific COBOL CICS program with the exact same "
        "input parameters, validations, and business logic."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(cards.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(bill_payment.router)
app.include_router(authorizations.router)
app.include_router(users.router)
app.include_router(transaction_types.router)


@app.get("/")
def root():
    return {
        "application": "CardDemo FastAPI",
        "version": "1.0.0",
        "description": "Converted from mainframe CICS programs",
        "endpoints": {
            "POST /api/auth/signin": "COSGN00C - User sign-on",
            "GET /api/accounts/{acct_id}": "COACTVWC - Account view",
            "PUT /api/accounts/{acct_id}": "COACTUPC - Account update",
            "GET /api/cards": "COCRDLIC - Card list",
            "GET /api/cards/{card_num}?acct_id=": "COCRDSLC - Card detail",
            "PUT /api/cards/{card_num}": "COCRDUPC - Card update",
            "GET /api/transactions": "COTRN00C - Transaction list",
            "GET /api/transactions/{tran_id}": "COTRN01C - Transaction detail",
            "POST /api/transactions": "COTRN02C - Add transaction",
            "POST /api/reports/submit": "CORPT00C - Submit report",
            "POST /api/bill-payments": "COBIL00C - Bill payment",
            "POST /api/authorizations/process": "COPAUA0C - Process authorization",
            "GET /api/authorizations/accounts/{acct_id}": "COPAUS0C - Auth summary",
            "GET /api/authorizations/{id}": "COPAUS1C - Auth detail",
            "PUT /api/authorizations/{id}/fraud": "COPAUS1C - Toggle fraud flag",
            "GET /api/users": "COUSR00C - User list",
            "POST /api/users": "COUSR01C - Add user",
            "PUT /api/users/{user_id}": "COUSR02C - Update user",
            "DELETE /api/users/{user_id}": "COUSR03C - Delete user",
            "GET /api/transaction-types": "COTRTLIC - Transaction type list",
            "GET /api/transaction-types/{type_cd}": "COTRTUPC - Get transaction type",
            "POST /api/transaction-types": "COTRTUPC - Add transaction type",
            "PUT /api/transaction-types/{type_cd}": "COTRTUPC - Update transaction type",
            "DELETE /api/transaction-types/{type_cd}": "COTRTUPC - Delete transaction type",
        },
    }
