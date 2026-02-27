#!/usr/bin/env python3
import json
import os
import urllib.error
import urllib.request


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main():
    resend_api_key = required_env("RESEND_API_KEY")
    email_from = required_env("EMAIL_FROM")
    email_to = required_env("EMAIL_TO")
    subject = os.getenv("EMAIL_SUBJECT", "Website change detected: bgwiedikon.ch/vermietungen")
    body_file = os.getenv("EMAIL_BODY_FILE", "email_body.txt")

    with open(body_file, "r", encoding="utf-8") as f:
        body = f.read()

    payload = {
        "from": email_from,
        "to": [email_to],
        "subject": subject,
        "html": f"<pre>{body}</pre>",
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "curl/8.7.1",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Resend API request failed: {e.code} {e.reason} - {error_body}") from e

    print(f"Notification email sent via Resend. Response: {resp_body}")


if __name__ == "__main__":
    main()
