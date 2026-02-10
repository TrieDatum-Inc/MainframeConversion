import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ReportRequest, ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/request", response_model=ReportResponse)
def request_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report_id = str(uuid.uuid4())[:16]
    return ReportResponse(
        report_id=report_id,
        report_type=request.report_type,
        status="queued",
        message=f"Report '{request.report_type}' has been queued for generation. "
        f"In production, this would trigger a Databricks job.",
    )
