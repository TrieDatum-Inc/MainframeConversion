# CardDemo UI - Next.js Frontend

A production-ready Next.js web application for the CardDemo Credit Card Management System. Integrates with the CardDemo FastAPI backend to provide a complete UI for all 20 CICS program equivalents.

## Tech Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **JWT Authentication**

## Prerequisites

- Node.js 18+ and npm
- CardDemo FastAPI backend running (default: `http://localhost:8000`)

## Setup

1. **Install dependencies:**

```bash
cd carddemo-ui
npm install
```

2. **Configure the API URL:**

Create a `.env.local` file (or edit the existing one):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Start the development server:**

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

4. **Build for production:**

```bash
npm run build
npm start
```

## Default Credentials

| User ID    | Password   | Role    |
|-----------|-----------|---------|
| ADMIN001  | ADMIN001  | Admin   |
| USER0001  | USER0001  | Regular |

## Pages & Features

### All Users

| Page | Route | Description | CICS Equivalent |
|------|-------|-------------|-----------------|
| Login | `/login` | Sign in with user ID and password | COSGN00C |
| Dashboard | `/` | Main menu with navigation to all features | COMEN01C |
| Account Lookup | `/accounts` | Enter account ID to view | - |
| Account View | `/accounts/{id}` | View account and customer details | COACTVWC |
| Account Edit | `/accounts/{id}/edit` | Update account and customer fields | COACTUPC |
| Card List | `/cards` | Paginated list with search filters | COCRDLIC |
| Card Detail | `/cards/{num}?acct_id=` | View card, account, and customer info | COCRDSLC |
| Card Edit | `/cards/{num}/edit?acct_id=` | Update card name, status, expiry | COCRDUPC |
| Transaction List | `/transactions` | Paginated list with filters | COTRN00C |
| Transaction Detail | `/transactions/{id}` | View full transaction details | COTRN01C |
| Add Transaction | `/transactions/new` | Create a new transaction | COTRN02C |
| Reports | `/reports` | Submit transaction report requests | CORPT00C |
| Bill Payment | `/bill-payment` | Pay full account balance | COBIL00C |
| Process Auth | `/authorizations/process` | Submit card authorization request | COPAUA0C |
| Auth Summary | `/authorizations/accounts/{id}` | View pending auths for an account | COPAUS0C |
| Auth Detail | `/authorizations/{id}` | View auth details and toggle fraud flag | COPAUS1C |

### Admin Only

| Page | Route | Description | CICS Equivalent |
|------|-------|-------------|-----------------|
| User List | `/admin/users` | List, search, and delete users | COUSR00C |
| Create User | `/admin/users/new` | Add new user | COUSR01C |
| Edit User | `/admin/users/{id}/edit` | Update user details | COUSR02C / COUSR03C |
| Transaction Type List | `/admin/transaction-types` | List and delete types | COTRTLIC |
| Create Type | `/admin/transaction-types/new` | Add new transaction type | COTRTUPC |
| Edit Type | `/admin/transaction-types/{cd}/edit` | Update transaction type | COTRTUPC |

## Architecture

```
carddemo-ui/
├── src/
│   ├── app/
│   │   ├── layout.tsx                 # Root layout
│   │   ├── login/page.tsx             # Login page (public)
│   │   └── (protected)/              # Protected route group
│   │       ├── layout.tsx             # Navbar + Sidebar + Auth check
│   │       ├── page.tsx               # Dashboard
│   │       ├── accounts/             # Account pages
│   │       ├── cards/                # Card pages
│   │       ├── transactions/         # Transaction pages
│   │       ├── reports/              # Report page
│   │       ├── bill-payment/         # Bill payment page
│   │       ├── authorizations/       # Authorization pages
│   │       └── admin/                # Admin-only pages
│   │           ├── users/
│   │           └── transaction-types/
│   ├── lib/
│   │   ├── api.ts                     # API client with JWT interceptor
│   │   └── types.ts                   # TypeScript interfaces
│   └── components/
│       ├── Navbar.tsx                 # Top navigation bar
│       ├── Sidebar.tsx                # Side navigation menu
│       └── ProtectedRoute.tsx         # Auth/admin route guard
├── .env.local                         # API URL configuration
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Authentication Flow

1. User signs in at `/login` with user ID and password
2. JWT token is received from `POST /api/auth/signin`
3. Token is stored in `localStorage` along with `user_id` and `user_type`
4. All subsequent API requests include `Authorization: Bearer <token>` header
5. On 401 response, user is redirected to login
6. Admin-only pages check `user_type === 'A'` before rendering

## API Endpoints Consumed

All endpoints require JWT authentication except `/api/auth/signin`.

- `POST /api/auth/signin` - Sign in
- `GET /api/accounts/{id}` - View account
- `PUT /api/accounts/{id}` - Update account
- `GET /api/cards` - List cards
- `GET /api/cards/{num}/{acct_id}` - Card detail
- `PUT /api/cards/{num}/{acct_id}` - Update card
- `GET /api/transactions` - List transactions
- `GET /api/transactions/{id}` - Transaction detail
- `POST /api/transactions` - Add transaction
- `POST /api/reports/submit` - Submit report
- `POST /api/bill-payments` - Pay bill
- `POST /api/authorizations/process` - Process auth
- `GET /api/authorizations/accounts/{id}` - Auth summary
- `GET /api/authorizations/{id}` - Auth detail
- `PUT /api/authorizations/{id}/fraud` - Toggle fraud
- `GET /api/users` - List users (admin)
- `POST /api/users` - Create user (admin)
- `GET /api/users/{id}` - Get user (admin)
- `PUT /api/users/{id}` - Update user (admin)
- `DELETE /api/users/{id}` - Delete user (admin)
- `GET /api/transaction-types` - List types (admin)
- `GET /api/transaction-types/{cd}` - Get type (admin)
- `POST /api/transaction-types` - Create type (admin)
- `PUT /api/transaction-types/{cd}` - Update type (admin)
- `DELETE /api/transaction-types/{cd}` - Delete type (admin)
