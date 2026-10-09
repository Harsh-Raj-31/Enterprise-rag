from email import message_from_string

import pytest

import app.security.email_service as email_service


def test_email_contains_reset_link(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            captured["host"] = host
            captured["port"] = port
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def ehlo(self):
            pass

        def starttls(self):
            captured["tls_enabled"] = True

        def login(self, username, password):
            captured["username"] = username
            captured["password"] = password

        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr(
        email_service.smtplib,
        "SMTP",
        FakeSMTP,
    )

    monkeypatch.setattr(
        email_service,
        "SMTP_USERNAME",
        "sender@example.com",
    )

    monkeypatch.setattr(
        email_service,
        "SMTP_PASSWORD",
        "test-password",
    )

    email_service.send_password_reset_email(
        recipient_email="recipient@example.com",
        reset_token="test-token-123",
    )

    message = captured["message"]

    assert captured["host"] == "smtp.gmail.com"
    assert captured["port"] == 587
    assert captured["tls_enabled"] is True
    assert captured["username"] == "sender@example.com"
    assert message["To"] == "recipient@example.com"
    assert "test-token-123" in message.get_content()
    assert "localhost:8501" in message.get_content()


def test_email_service_rejects_missing_credentials(monkeypatch):
    monkeypatch.setattr(
        email_service,
        "SMTP_USERNAME",
        None,
    )

    monkeypatch.setattr(
        email_service,
        "SMTP_PASSWORD",
        None,
    )

    with pytest.raises(RuntimeError):
        email_service.send_password_reset_email(
            recipient_email="recipient@example.com",
            reset_token="test-token",
        )