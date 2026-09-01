from typing import Any, Mapping

import pytest
from pydantic import ValidationError

from receipt_mailer.receipt_sender import ReceiptRequest, send_course_receipt


class RecordingGateway:
    def __init__(self) -> None:
        self.sent: dict[str, Any] = {}
        self.looked_up = ""

    def email_send(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> Mapping[str, Any]:
        self.sent = {
            "to": to,
            "subject": subject,
            "html": html,
            "idempotency_key": idempotency_key,
        }
        return {"message_id": "msg_edu_42"}

    def email_get(self, message_id: str) -> Mapping[str, Any]:
        self.looked_up = message_id
        return {"message_id": message_id, "status": "sent"}


def request_data() -> dict[str, str]:
    return {
        "order_id": "EDU-42",
        "learner_email": "learner@example.org",
        "learner_name": "Mina Chen",
        "course_title": "Reliable Python Services",
        "course_access_url": "https://learn.example.org/course/42",
        "amount": "149.00",
        "currency": "USD",
        "learner_deadline": "2026-09-30",
        "educator_report_due": "2026-10-02",
    }


def test_receipt_carries_delivery_deadlines_into_email_and_lookup() -> None:
    gateway = RecordingGateway()

    result = send_course_receipt(ReceiptRequest(**request_data()), gateway)

    assert "2026-09-30" in gateway.sent["html"]
    assert "2026-10-02" in gateway.sent["html"]
    assert gateway.sent["idempotency_key"] == "course-order:EDU-42"
    assert gateway.looked_up == "msg_edu_42"
    assert result.delivery["status"] == "sent"


def test_educator_report_cannot_precede_learner_deadline() -> None:
    data = request_data()
    data["educator_report_due"] = "2026-09-29"

    with pytest.raises(ValidationError, match="on or after learner_deadline"):
        ReceiptRequest(**data)
