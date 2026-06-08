import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from app.core.config import get_settings


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_alert(self, subject: str, body: str) -> tuple[str, str | None]:
        if not self.settings.smtp_ready:
            return "skipped", "SMTP 未配置，已跳过邮件发送。"

        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = formataddr((self.settings.app_name, self.settings.smtp_sender))
        message["To"] = self.settings.alert_recipient

        try:
            with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.sendmail(self.settings.smtp_sender, [self.settings.alert_recipient], message.as_string())
            return "sent", None
        except Exception as exc:  # pragma: no cover - network path
            return "failed", str(exc)

