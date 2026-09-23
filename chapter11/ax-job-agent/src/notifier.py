"""STEP 12/13: Slack Incoming Webhook, Gmail SMTP(smtp.gmail.com:587, STARTTLS)로 보고서 발송.

SLACK_PROD_WEBHOOK_URL / GMAIL_USER / GMAIL_APP_PASSWORD는 .env에서만 읽고, 코드에 쓰거나 출력하지 않는다.
"""

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import requests

from src.gemini_client import load_env

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SLACK_MAX_CHARS = 3500  # Slack은 text가 4,000자를 넘으면 잘리므로 여유를 둔다
SLACK_TRUNCATED_NOTE = "\n\n...전체는 이메일 참고"


def fit_slack_text(message, max_chars=SLACK_MAX_CHARS):
    """길이 제한을 넘으면 앞부분만 남기고 안내 문구를 붙인다."""
    if len(message) <= max_chars:
        return message
    return message[: max_chars - len(SLACK_TRUNCATED_NOTE)].rstrip() + SLACK_TRUNCATED_NOTE


def send_slack(message):
    """Slack Incoming Webhook으로 text 메시지 1건을 보내고 HTTP status code를 돌려준다."""
    load_env()
    webhook_url = os.getenv("SLACK_PROD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("SLACK_PROD_WEBHOOK_URL이 없다. .env에 넣는다.")

    # requests의 에러 메시지에는 요청 URL(= Webhook 비밀값)이 들어가므로, URL 없이 다시 던진다
    try:
        response = requests.post(webhook_url, json={"text": fit_slack_text(message)}, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(f"Slack 요청 실패 ({type(e).__name__})") from None
    if response.status_code != 200:
        raise RuntimeError(f"Slack 발송 실패: HTTP {response.status_code} {response.text[:100]}")
    return response.status_code


def send_gmail(subject, body, attachment_path=None, to_addr=None):
    """메일 1통을 보낸다. to_addr를 안 주면 GMAIL_USER 본인에게 보낸다."""
    load_env()
    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_user or not gmail_app_password:
        raise RuntimeError("GMAIL_USER / GMAIL_APP_PASSWORD가 없다. .env에 넣는다.")

    msg = EmailMessage()
    msg["From"] = gmail_user
    msg["To"] = to_addr or gmail_user
    msg["Subject"] = subject
    msg.set_content(body)  # 본문: Markdown 원문을 일반 텍스트로
    if attachment_path is not None:
        msg.add_attachment(
            Path(attachment_path).read_bytes(),
            maintype="text",
            subtype="markdown",
            filename=Path(attachment_path).name,
        )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(gmail_user, gmail_app_password)  # 앱 비밀번호는 여기서만 쓰고 출력하지 않는다
        server.send_message(msg)
