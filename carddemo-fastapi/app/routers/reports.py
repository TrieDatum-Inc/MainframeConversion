from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import ReportSubmitRequest, ReportSubmitResponse
from app.services.report_service import submit_report

router = APIRouter(prefix="/api/reports", tags=["Reports (CORPT00C)"])


@router.post("/submit", response_model=ReportSubmitResponse)
def submit_report_endpoint(request: ReportSubmitRequest, current_user: User = Depends(get_current_user)):
    data = request.model_dump()
    return submit_report(data)
