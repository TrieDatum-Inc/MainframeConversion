# CardDemo FastAPI

FastAPI REST API conversion of the CardDemo mainframe CICS programs. Each endpoint maps to a specific COBOL CICS program with the same input parameters, validations, and business logic.

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)
- MySQL 8.0+ (or MariaDB 10.5+)

## Project Structure

```
carddemo-fastapi/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py             # Configuration (DB URL, JWT settings)
│   ├── database.py           # SQLAlchemy engine and session
│   ├── models/
│   │   └── models.py         # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py        # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py           # COSGN00C - Sign-on
│   │   ├── accounts.py       # COACTVWC/COACTUPC - Account view/update
│   │   ├── cards.py          # COCRDLIC/COCRDSLC/COCRDUPC - Card list/detail/update
│   │   ├── transactions.py   # COTRN00C/COTRN01C/COTRN02C - Transaction list/detail/add
│   │   ├── reports.py        # CORPT00C - Report submission
│   │   ├── bill_payment.py   # COBIL00C - Bill payment
│   │   ├── authorizations.py # COPAUA0C/COPAUS0C/COPAUS1C - Authorization subsystem
│   │   ├── users.py          # COUSR00C-03C - User CRUD
│   │   └── transaction_types.py # COTRTLIC/COTRTUPC - Transaction type CRUD
│   └── services/
│       ├── auth_service.py
│       ├── account_service.py
│       ├── card_service.py
│       ├── transaction_service.py
│       ├── report_service.py
│       ├── bill_payment_service.py
│       ├── authorization_service.py
│       ├── user_service.py
│       └── transaction_type_service.py
├── seed.py                   # Sample data seeder
├── pyproject.toml            # Poetry dependencies
├── poetry.lock
├── requirements.txt          # Pip-compatible dependencies
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
cd carddemo-fastapi
poetry install
```

### 2. Create MySQL Database

```sql
CREATE DATABASE carddemo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'carddemo'@'localhost' IDENTIFIED BY 'carddemo_password';
GRANT ALL PRIVILEGES ON carddemo.* TO 'carddemo'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Configure Environment

Create a `.env` file in the `carddemo-fastapi/` directory:

```env
DATABASE_URL=mysql+pymysql://carddemo:carddemo_password@localhost:3306/carddemo
SECRET_KEY=your-secret-key-change-in-production
```

### 4. Seed Sample Data

This creates all tables and populates them with sample data:

```bash
poetry run python seed.py
```

Sample credentials after seeding:
- **Admin**: `user_id=ADMIN001`, `password=ADMIN001`
- **User**: `user_id=USER0001`, `password=USER0001`

Sample data includes:
- 5 accounts (10000000001 - 10000000005)
- 6 cards (4111111111111111, 5333333333333333, etc.)
- 5 customers
- 10 transactions
- 10 transaction types
- Pending authorization records

### 5. Run the Application

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## Swagger Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## API Endpoints

### Authentication (COSGN00C)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signin` | User sign-on (validates user_id + password) |

### Accounts (COACTVWC, COACTUPC)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/accounts/{acct_id}` | View account details (read-only) |
| PUT | `/api/accounts/{acct_id}` | Update account and customer data |

### Cards (COCRDLIC, COCRDSLC, COCRDUPC)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cards` | List cards (paginated, optional acct_id/card_num filters) |
| GET | `/api/cards/{card_num}?acct_id={id}` | View card detail (both params required) |
| PUT | `/api/cards/{card_num}` | Update card (name, status, expiry) |

### Transactions (COTRN00C, COTRN01C, COTRN02C)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions` | List transactions (paginated, optional filters) |
| GET | `/api/transactions/{tran_id}` | View transaction detail |
| POST | `/api/transactions` | Add new transaction |

### Reports (CORPT00C)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/reports/submit` | Submit report job (returns job ID) |

### Bill Payment (COBIL00C)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bill-payments` | Pay full account balance |

### Authorizations (COPAUA0C, COPAUS0C, COPAUS1C)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/authorizations/process` | Process card authorization request |
| GET | `/api/authorizations/accounts/{acct_id}` | View pending auth summary + list |
| GET | `/api/authorizations/{id}` | View authorization detail |
| PUT | `/api/authorizations/{id}/fraud` | Toggle fraud flag |

### Users (COUSR00C, COUSR01C, COUSR02C, COUSR03C)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | List users (paginated, optional user_id filter) |
| GET | `/api/users/{user_id}` | Get user details |
| POST | `/api/users` | Add new user |
| PUT | `/api/users/{user_id}` | Update user |
| DELETE | `/api/users/{user_id}` | Delete user |

### Transaction Types (COTRTLIC, COTRTUPC)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transaction-types` | List transaction types (paginated) |
| GET | `/api/transaction-types/{type_cd}` | Get transaction type |
| POST | `/api/transaction-types` | Add transaction type |
| PUT | `/api/transaction-types/{type_cd}` | Update transaction type |
| DELETE | `/api/transaction-types/{type_cd}` | Delete transaction type |

## COBOL Program to Endpoint Mapping

| COBOL Program | CICS Tran ID | FastAPI Endpoint | Function |
|---------------|-------------|------------------|----------|
| COSGN00C | CSGN | POST /api/auth/signin | User sign-on |
| COACTVWC | CAVW | GET /api/accounts/{id} | Account view |
| COACTUPC | CAUP | PUT /api/accounts/{id} | Account/customer update |
| COCRDLIC | CCLI | GET /api/cards | Card list |
| COCRDSLC | CCDL | GET /api/cards/{num}?acct_id= | Card detail |
| COCRDUPC | CCUP | PUT /api/cards/{num} | Card update |
| COTRN00C | CT00 | GET /api/transactions | Transaction list |
| COTRN01C | CT01 | GET /api/transactions/{id} | Transaction detail |
| COTRN02C | CT02 | POST /api/transactions | Add transaction |
| CORPT00C | CR00 | POST /api/reports/submit | Submit report |
| COBIL00C | CB00 | POST /api/bill-payments | Bill payment |
| COPAUA0C | CP00 | POST /api/authorizations/process | Auth decision |
| COPAUS0C | CPVS | GET /api/authorizations/accounts/{id} | Auth summary |
| COPAUS1C | CPVD | GET/PUT /api/authorizations/{id} | Auth detail/fraud |
| COUSR00C | CU00 | GET /api/users | User list |
| COUSR01C | CU01 | POST /api/users | Add user |
| COUSR02C | CU02 | PUT /api/users/{id} | Update user |
| COUSR03C | CU03 | DELETE /api/users/{id} | Delete user |
| COTRTLIC | CTLI | GET /api/transaction-types | Transaction type list |
| COTRTUPC | CTTU | CRUD /api/transaction-types/{cd} | Transaction type CRUD |

## Database Tables

| Table | Source Copybook | COBOL Record | Description |
|-------|----------------|-------------|-------------|
| accounts | CVACT01Y | ACCOUNT-RECORD (300 bytes) | Account master |
| cards | CVACT02Y | CARD-RECORD (150 bytes) | Card master |
| customers | CUSTREC | CUSTOMER-RECORD (500 bytes) | Customer master |
| card_xref | CVACT03Y | CARD-XREF-RECORD (50 bytes) | Card cross-reference |
| transactions | CVTRA05Y | TRAN-RECORD (350 bytes) | Transaction master |
| users | CSUSR01Y | SEC-USER-DATA (80 bytes) | User security |
| transaction_types | DB2 TRAN_TYPE | TRANSACTION_TYPE (60 bytes) | Transaction types |
| pending_auth_summary | IMS PAUTSUM0 | Auth summary segment | Auth summary |
| pending_auth_details | IMS PAUTHDB | Auth detail segment | Auth details |

## Notes

- **Validation messages** match the exact COBOL error messages (e.g., "Please enter User ID ...", "Acct ID can NOT be zeros...")
- **COTRN02C** intentionally does NOT validate transaction amount against account balance (matches COBOL behavior; the batch program CBTRN02C handles that validation)
- **CORPT00C** is a stub that returns a job ID; the actual report generation would be handled by a batch process
- **COBIL00C** pays the full current balance (no partial payments), matching the COBOL program behavior
- **Authorization subsystem** (COPAUA0C/COPAUS0C/COPAUS1C) was converted from IMS hierarchical database to relational MySQL tables
- Passwords are stored in plaintext to match the COBOL USRSEC file behavior; production deployments should add hashing
