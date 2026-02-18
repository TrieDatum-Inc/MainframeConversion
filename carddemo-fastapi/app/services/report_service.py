import uuid


def submit_report(data: dict) -> dict:
    start_date = f"{data['start_year']}-{data['start_month']:02d}-01"
    end_date = f"{data['end_year']}-{data['end_month']:02d}-01"
    job_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"

    return {
        "message": f"Report job {job_id} submitted successfully. "
                   f"Report type: {data['report_type']}",
        "job_id": job_id,
        "report_type": data["report_type"],
        "start_date": start_date,
        "end_date": end_date,
    }
