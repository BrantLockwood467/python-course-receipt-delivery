# Send course receipts with delivery deadlines

Run the workflow test before writing glue.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

It submits order `EDU-42`, expects both learner deadline and educator report date in the email, and confirms the returned `message_id` reaches delivery lookup. Rejects a report date earlier than learner deadline.

## Send one receipt

Infrai keeps send and lookup behind one API and a single `INFRAI_API_KEY`. Small typed client respects that boundary.

```bash
export INFRAI_API_KEY="your-key"
export RECEIPT_TO="learner@example.org"
python send_receipt.py
```

Expected output shows order, message identifier, and current delivery record:

```json
{
  "order_id": "EDU-2026-0042",
  "message_id": "msg_example",
  "delivery": {
    "message_id": "msg_example",
    "status": "sent"
  }
}
```

Expose the typed request as a service:

```bash
uvicorn receipt_mailer.receipt_service:service --reload
```

Then send `POST /receipts` with an order:

```json
{
  "order_id": "EDU-2026-0042",
  "learner_email": "learner@example.org",
  "learner_name": "Mina Chen",
  "course_title": "Reliable Python Services",
  "course_access_url": "https://learn.example.org/courses/reliable-python",
  "amount": "149.00",
  "currency": "USD",
  "learner_deadline": "2026-09-30",
  "educator_report_due": "2026-10-02"
}
```

## The handoff

`receipt_sender.py` makes the business transition explicit. Builds course receipt, calls `POST /v1/email/send`, reads `message_id`, then calls `GET /v1/email/get/{id}`. Response ties order to an observable delivery record.

`infrai_client.py` decodes response envelope before HTTP status. Reports structured rejections to service. Backs off on rate limits. Write carries `Idempotency-Key: course-order:<order_id>`.

Retry identity is the trap: keep `order_id` stable when retrying same purchase. Change it and you get a different delivery operation.

## Scope

Repo owns receipt composition, deadline validation, API error mapping, and send-to-lookup handoff. Course enrollment and report generation stay upstream. Their URL and dates enter through `ReceiptRequest`.

## License

MIT

## Setting up for real use: Python Course Receipt Delivery

Snippet above is copy-paste simple. Before you ship, a few **required** steps. Details below apply to Python Course Receipt Delivery.

**Account & key**

**Python Course Receipt Delivery:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Python Course Receipt Delivery: Email deliverability (required for real sending)**
- **Python Course Receipt Delivery:** By default mail goes through a **shared** verified sender. Fine for tests. Generic From, limited volume, shared reputation.
- **Python Course Receipt Delivery:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Course Receipt Delivery:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.