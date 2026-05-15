"""Unit-test conftest — overrides the session-scoped DB fixture.

Unit tests are pure-Python and require no database connection.
This local conftest shadows the autouse ``create_tables`` fixture from the
parent conftest so that pytest does not attempt to reach PostgreSQL.
"""
from __future__ import annotations

import pytest_asyncio


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():  # noqa: PT004
    """No-op override: unit tests need no database."""
    yield
