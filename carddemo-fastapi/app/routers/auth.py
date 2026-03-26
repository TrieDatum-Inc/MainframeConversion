from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import SignonRequest, SignonResponse
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/api/auth", tags=["Authentication (COSGN00C)"])


@router.post("/signin", response_model=SignonResponse)
def signin(request: SignonRequest, db: Session = Depends(get_db)):
    return authenticate_user(db, request.user_id, request.password)
