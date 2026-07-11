#!/usr/bin/env python3
"""send_notification.py — email alert with attachment (stdlib only).

Secrets (GitHub Actions -> Settings -> Secrets), per data/docs/SMTP_Setup_Guide.md:
  SMTP_HOST (smtp.gmail.com), SMTP_PORT (465), SMTP_USERNAME, SMTP_PASSWORD
  (Gmail App Password, NOT the account password), MAIL_TO.

Behavior: if SMTP_PASSWORD is unset, prints a NOT-CONFIGURED warning and exits 0
(so the pipeline runs before secrets are set). Any real send failure exits 1 —
a broken email must surface in the Actions run.
"""
import argparse, json, os, smtplib, ssl, sys
from email.message import EmailMessage
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attach", action="append", default=[], help="file(s) to attach")
    ap.add_argument("--summary-json", help="scanner summary json (from scanner.py stdout)")
    ap.add_argument("--subject", default=None)
    a = ap.parse_args()

    pwd = os.environ.get("SMTP_PASSWORD", "")
    if not pwd:
        print("send_notification: SMTP secrets not configured — skipping email "
              "(see data/docs/SMTP_Setup_Guide.md)", file=sys.stderr)
        return 0

    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ["SMTP_USERNAME"]
    to = os.environ.get("MAIL_TO", user)

    n_new, date = "?", "?"
    if a.summary_json and Path(a.summary_json).exists():
        s = json.loads(Path(a.summary_json).read_text())
        n_new, date = s.get("appended", "?"), s.get("date", "?")

    msg = EmailMessage()
    msg["Subject"] = a.subject or f"[Japan M&A] {n_new} new record(s) — {date}"
    msg["From"], msg["To"] = user, to
    body = [f"Daily scan {date}: {n_new} new record(s) appended to Japan_new.csv.",
            "Attached: latest transformed dataset.",
            "Review new records and use the add-deal button/CLI to promote landmarks."]
    msg.set_content("\n".join(body))

    for f in a.attach:
        p = Path(f)
        if not p.exists():
            print(f"send_notification: missing attachment {f}", file=sys.stderr)
            return 1
        msg.add_attachment(p.read_bytes(), maintype="text", subtype="csv", filename=p.name)

    try:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
            s.login(user, pwd)
            s.send_message(msg)
        print(f"send_notification: sent to {to} ({len(a.attach)} attachment(s))")
        return 0
    except Exception as e:
        print(f"send_notification: SEND FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
