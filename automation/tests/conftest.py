"""Shared test fixtures."""
import pytest

from fmro_auto.core.config import Settings


@pytest.fixture
def test_settings():
    return Settings()
