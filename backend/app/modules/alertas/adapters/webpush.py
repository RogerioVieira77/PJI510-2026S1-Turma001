"""VAPID/Web Push adapter — TASK-63."""
from __future__ import annotations

import json

import structlog
from pywebpush import WebPushException, webpush

from app.config import get_settings

log = structlog.get_logger()


class PushAdapter:
    @staticmethod
    def send(subscription: dict, payload: dict) -> bool:
        """Send a Web Push notification via VAPID.

        Args:
            subscription: dict with keys ``endpoint``, ``keys.p256dh``, ``keys.auth``
            payload:       notification payload (will be JSON-serialised)

        Returns:
            True on success.

        Raises:
            WebPushException: propagated so the caller can handle 410 Gone
                              (expired subscription) and remove it from the DB.
        """
        settings = get_settings()
        webpush(
            subscription_info=subscription,
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
            content_encoding="aesgcm",
        )
        return True
