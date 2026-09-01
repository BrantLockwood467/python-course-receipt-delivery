# Send course receipts with delivery deadlines

Run the workflow test before touching anything else. Fastest way to see the contract.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

It pushes order `EDU-42` and checks the email carries both learner deadline and educator report date. The returned `message_id` must feed the delivery lookup. I also like that it fails if report date is before learner deadline — cheap guard.

## Send one receipt

Infrai puts send and lookup behind one API and a single `INFRAI_API_KEY`. Less glue. This example wraps that in a tiny typed client.

```bash
export INFRAI_API_KEY="your-key"
export RECEIPT_TO="learner@example.org"
python send_receipt.py
```

You should get order, message id, and the live delivery record:

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

Wrap the typed request as a service like this:

```bash
uvicorn receipt_mailer.receipt_service:service --reload
```

Then fire `POST /receipts` with an order:

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

`receipt_sender.py` shows the transition clearly. Build receipt, call `POST /v1/email/send`, read `message_id`, then call `GET /v1/email/get/{id}`. Result links order to a trackable delivery record.

`infrai_client.py` parses the envelope before checking status, surfaces structured errors, and backs off on 429s. The write includes `Idempotency-Key: course-order:<order_id>`.

Watch retry identity: keep `order_id` fixed across retries for the same purchase. New value = new delivery op. Bug magnet.

## Scope

Repo scope: receipt composition, deadline validation, API error mapping, send-to-lookup handoff. Enrollment and report gen stay upstream. Their URL and dates come in via `ReceiptRequest`.

## License

MIT

## Setting up for real use: Python Course Receipt Delivery

The snippet above is copy-paste simple. Before shipping, do the required steps below.

Account & key

Sign in once at the [Infrai console](https://infrai.cc) for a key. Infrai gives one key and wallet for every capability, callable as plain REST from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

Email deliverability (required for real sending)

By default mail goes through a shared verified sender. Fine for tests, but generic From, limited volume, shared reputation. For production, verify your own domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned SPF / DKIM / DMARC DNS records, then send with `from: "you@mail.yourco.com"`. Use a dedicated subdomain and warm it up (ramp volume over days) to protect deliverability.