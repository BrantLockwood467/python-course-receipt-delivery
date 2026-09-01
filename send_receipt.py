import json
import os

from receipt_mailer.infrai_client import InfraiClient
from receipt_mailer.receipt_sender import ReceiptRequest, send_course_receipt


def main() -> None:
    request = ReceiptRequest(
        order_id="EDU-2026-0042",
        learner_email=os.environ["RECEIPT_TO"],
        learner_name="Mina Chen",
        course_title="Reliable Python Services",
        course_access_url="https://learn.example.org/courses/reliable-python",
        amount="149.00",
        currency="USD",
        learner_deadline="2026-09-30",
        educator_report_due="2026-10-02",
    )
    with InfraiClient() as gateway:
        result = send_course_receipt(request, gateway)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
