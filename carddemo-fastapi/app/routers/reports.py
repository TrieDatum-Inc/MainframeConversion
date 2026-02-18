from fastapi import APIRouter

from app.schemas.schemas import ReportSubmitRequest, ReportSubmitResponse
from app.services.report_service import submit_report

router = APIRouter(prefix="/api/reports", tags=["Reports (CORPT00C)"])


@router.post("/submit", response_model=ReportSubmitResponse)
def submit_report_endpoint(request: ReportSubmitRequest):
    data = request.model_dump()
    return submit_report(data)
