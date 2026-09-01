from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .receipt_sender import ReceiptRequest, ReceiptResult, send_course_receipt

service = FastAPI(title="Course receipt mailer")


@service.post("/receipts", response_model=ReceiptResult, status_code=201)
def create_receipt(request: ReceiptRequest) -> ReceiptResult:
    try:
        with InfraiClient() as gateway:
            return send_course_receipt(request, gateway)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "detail": dict(exc.detail)},
        ) from exc
