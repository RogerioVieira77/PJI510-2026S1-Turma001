#!/usr/bin/env python3
"""
Gera par de chaves VAPID para Web Push e imprime as variáveis prontas para o .env.

Uso:
    pip install py_vapid
    python scripts/generate_vapid_keys.py
"""
from __future__ import annotations

import base64

from py_vapid import Vapid


def main() -> None:
    vapid = Vapid()
    vapid.generate_keys()

    private_der = vapid.private_key.private_bytes(
        encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.DER,
        format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PrivateFormat"]).PrivateFormat.PKCS8,
        encryption_algorithm=__import__("cryptography.hazmat.primitives.serialization", fromlist=["NoEncryption"]).NoEncryption(),
    )
    public_der = vapid.public_key.public_bytes(
        encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.X962,
        format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PublicFormat"]).PublicFormat.UncompressedPoint,
    )

    private_b64 = base64.urlsafe_b64encode(private_der).rstrip(b"=").decode()
    public_b64 = base64.urlsafe_b64encode(public_der).rstrip(b"=").decode()

    print("Adicione ao seu .env:\n")
    print(f"VAPID_PUBLIC_KEY={public_b64}")
    print(f"VAPID_PRIVATE_KEY={private_b64}")


if __name__ == "__main__":
    main()
