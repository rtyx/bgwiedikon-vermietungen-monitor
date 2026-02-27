#!/usr/bin/env python3
import os
import smtplib
import ssl
from email.message import EmailMessage


def required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main():
    smtp_host = required_env("SMTP_HOST")
    smtp_port = int(required_env("SMTP_PORT"))
    smtp_username = required_env("SMTP_USERNAME")
    smtp_password = required_env("SMTP_PASSWORD")
    email_from = required_env("EMAIL_FROM")
    email_to = required_env("EMAIL_TO")
    subject = os.getenv("EMAIL_SUBJECT", "Website change detected: bgwiedikon.ch/vermietungen")
    body_file = os.getenv("EMAIL_BODY_FILE", "email_body.txt")

    with open(body_file, "r", encoding="utf-8") as f:
        body = f.read()

    msg = EmailMessage()
    msg["From"] = email_from
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.set_content(body)

    if smtp_port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=30) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

    print("Notification email sent.")


if __name__ == "__main__":
    main()
