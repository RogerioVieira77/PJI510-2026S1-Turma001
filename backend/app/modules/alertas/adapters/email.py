"""Email (aiosmtplib) adapter — TASK-64."""
from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import structlog

from app.config import get_settings

log = structlog.get_logger()


class EmailAdapter:
    @staticmethod
    async def send(to: str, subject: str, body_html: str) -> None:
        """Send an HTML email via SMTP (async, STARTTLS or SSL).

        Raises:
            aiosmtplib.SMTPException: on delivery failure.
        """
        settings = get_settings()
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM or settings.SMTP_USER
        message["To"] = to
        message.attach(MIMEText(body_html, "html", "utf-8"))

        smtp_kwargs: dict = {
            "hostname": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
        }
        if settings.SMTP_USER:
            smtp_kwargs["username"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            smtp_kwargs["password"] = settings.SMTP_PASSWORD

        if settings.SMTP_TLS:
            # STARTTLS upgrade (port 587)
            smtp_kwargs["start_tls"] = True
        else:
            # Implicit TLS (port 465)
            smtp_kwargs["use_tls"] = True

        await aiosmtplib.send(message, **smtp_kwargs)


_CONFIRM_TEMPLATE = """\
<!DOCTYPE html>
<html lang="pt-BR">
<body>
  <p>Olá,</p>
  <p>Confirme sua assinatura de alertas do <strong>PiscinãoMonitor</strong>:</p>
  <p><a href="{confirm_url}">Confirmar assinatura</a></p>
  <p>Se você não solicitou isso, ignore este e-mail.</p>
  <hr/>
  <p><small><a href="{unsubscribe_url}">Descadastrar</a></small></p>
</body>
</html>
"""

_ALERTA_TEMPLATE = """\
<!DOCTYPE html>
<html lang="pt-BR">
<body>
  <p><strong>Alerta PisciniaoMonitor</strong></p>
  <p>Reservatório: <strong>{reservatorio_nome}</strong></p>
  <p>Nível: <strong>{nivel_label}</strong> ({nivel_pct:.1f}%)</p>
  <p>{mensagem}</p>
  <hr/>
  <p><small><a href="{unsubscribe_url}">Descadastrar</a></small></p>
</body>
</html>
"""


def render_confirm_email(confirm_url: str, unsubscribe_url: str) -> str:
    return _CONFIRM_TEMPLATE.format(
        confirm_url=confirm_url, unsubscribe_url=unsubscribe_url
    )


def render_alerta_email(
    reservatorio_nome: str,
    nivel_label: str,
    nivel_pct: float,
    mensagem: str,
    unsubscribe_url: str,
) -> str:
    return _ALERTA_TEMPLATE.format(
        reservatorio_nome=reservatorio_nome,
        nivel_label=nivel_label,
        nivel_pct=nivel_pct,
        mensagem=mensagem,
        unsubscribe_url=unsubscribe_url,
    )
