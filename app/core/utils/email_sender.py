# app/core/utils/email_sender.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from app.core.config.project_config import settings


class NotificationType(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    SUCCESS = "SUCCESS"
    SHUTDOWN = "SHUTDOWN"


class EmailSender:
    def __init__(self):
        self.smtp_host = settings.EMAIL_HOST
        self.smtp_port = settings.EMAIL_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.from_email = settings.EMAIL_FROM
        self.use_tls = settings.EMAIL_USE_TLS
        self.use_ssl = settings.EMAIL_USE_SSL

    async def send_email(self, to_email: str, subject: str, body: str):
        """
        Отправляет электронное письмо

        :param to_email: Адрес получателя
        :param subject: Тема письма
        :param body: Текст письма
        """
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            if self.use_ssl:
                # For SSL connections (like Yandex on port 465)
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                # For TLS connections (like Gmail on port 587)
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                if self.use_tls:
                    server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
        except Exception as e:
            print(f"Ошибка при отправке электронного письма: {e}")
            raise


async def send_notification(
    message: str,
    notification_type: NotificationType = NotificationType.ERROR,
    additional_info: str = "",
    worker_name: str = "ARQ Worker"
):
    """
    Sends email notifications for different types of events in the workers.

    Args:
        message: Main message content
        notification_type: Type of notification (ERROR, WARNING, SUCCESS, SHUTDOWN)
        additional_info: Additional information to include in the message
        worker_name: Name of the worker sending the notification
    """
    email_sender = EmailSender()
    to_email = settings.EMAIL_ADMIN

    # Create appropriate subject based on notification type
    type_to_subject = {
        NotificationType.ERROR: f"Ошибка воркера {worker_name}",
        NotificationType.WARNING: f"Предупреждение от воркера {worker_name}",
        NotificationType.SUCCESS: f"Уведомление от воркера {worker_name}",
        NotificationType.SHUTDOWN: f"Остановка воркера {worker_name}"
    }

    subject = type_to_subject.get(notification_type, f"Уведомление от воркера {worker_name}")

    # Create body with appropriate formatting based on notification type
    type_to_body_prefix = {
        NotificationType.ERROR: f"Произошла критическая ошибка при выполнении задачи воркера {worker_name}:\n\n",
        NotificationType.WARNING: f"Обнаружена некритичная ошибка при выполнении задачи воркера {worker_name}, "
        f"воркер продолжает работу:\n\n",
        NotificationType.SUCCESS: f"Нормальное завершение или уведомление от воркера {worker_name}:\n\n",
        NotificationType.SHUTDOWN: f"Воркер {worker_name} завершает работу:\n\n"
    }

    body_prefix = type_to_body_prefix.get(notification_type, f"Уведомление от воркера {worker_name}:\n\n")

    body = body_prefix + message

    if additional_info:
        body += f"\n\nДополнительная информация: {additional_info}"

    await email_sender.send_email(to_email, subject, body)
