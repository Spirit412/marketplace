import logging
from email.mime.text import MIMEText

import aiosmtplib

from src.config.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Thin async wrapper around aiosmtplib for sending transactional emails."""

    def __init__(self) -> None:
        self._settings = settings

    async def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = True,
    ) -> bool:
        try:
            msg = MIMEText(body, "html" if html else "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = self._settings.SMTP_FROM_EMAIL
            msg["To"] = to_email

            await aiosmtplib.send(
                msg,
                hostname=self._settings.SMTP_HOST,
                port=self._settings.SMTP_PORT,
                username=self._settings.SMTP_USER or None,
                password=self._settings.SMTP_PASSWORD or None,
                start_tls=True,
            )
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception as exc:
            logger.exception("Failed to send email to %s: %s", to_email, exc)
            return False
