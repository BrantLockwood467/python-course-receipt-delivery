from __future__ import annotations

from datetime import date
from decimal import Decimal
from html import escape
from typing import Any, Mapping, Protocol

from pydantic import BaseModel, EmailStr, Field, model_validator


class ReceiptRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=80)
    learner_email: EmailStr
    learner_name: str = Field(min_length=1, max_length=120)
    course_title: str = Field(min_length=1, max_length=200)
    course_access_url: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    learner_deadline: date
    educator_report_due: date

    @model_validator(mode="after")
    def report_follows_learner_deadline(self) -> ReceiptRequest:
        if self.educator_report_due < self.learner_deadline:
            raise ValueError("educator_report_due must be on or after learner_deadline")
        return self


class ReceiptResult(BaseModel):
    order_id: str
    message_id: str
    delivery: Mapping[str, Any]


class EmailGateway(Protocol):
    def email_send(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> Mapping[str, Any]:
        raise AssertionError("protocol method")

    def email_get(self, message_id: str) -> Mapping[str, Any]:
        raise AssertionError("protocol method")


def send_course_receipt(
    request: ReceiptRequest, gateway: EmailGateway
) -> ReceiptResult:
    subject = f"Receipt {request.order_id}: {request.course_title}"
    html = _render_receipt(request)
    sent = gateway.email_send(
        to=request.learner_email,
        subject=subject,
        html=html,
        idempotency_key=f"course-order:{request.order_id}",
    )
    message_id = str(sent["message_id"])
    delivery = gateway.email_get(message_id)
    return ReceiptResult(
        order_id=request.order_id,
        message_id=message_id,
        delivery=delivery,
    )


def _render_receipt(request: ReceiptRequest) -> str:
    return (
        f"<h1>Course receipt</h1>"
        f"<p>Order: {escape(request.order_id)}</p>"
        f"<p>Learner: {escape(request.learner_name)}</p>"
        f"<p>Course: {escape(request.course_title)}</p>"
        f"<p>Paid: {request.currency} {request.amount:.2f}</p>"
        f"<p>Start learning: <a href=\"{escape(request.course_access_url, quote=True)}\">"
        f"open course</a></p>"
        f"<p>Learner deadline: {request.learner_deadline.isoformat()}</p>"
        f"<p>Educator report due: {request.educator_report_due.isoformat()}</p>"
    )
