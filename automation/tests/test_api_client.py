"""Tests for the FMRO API client (requires backend running)."""
import pytest

from fmro_auto.core.api_client import FMROClient


@pytest.fixture
def client():
    c = FMROClient()
    yield c
    c.close()


class TestFMROClient:
    def test_health(self, client: FMROClient):
        result = client.health()
        assert result.get("ok") == "true"

    def test_list_companies(self, client: FMROClient):
        result = client.list_companies()
        assert isinstance(result, list)

    def test_list_jobs(self, client: FMROClient):
        result = client.list_jobs()
        assert isinstance(result, list)

    def test_list_review_queue(self, client: FMROClient):
        result = client.list_review_queue(status="pending")
        assert isinstance(result, list)

    def test_submit_to_review_queue(self, client: FMROClient):
        result = client.submit_to_review_queue(
            source_type="test",
            payload={
                "companyName": "Test Corp",
                "title": "Test Position",
                "location": "Beijing",
                "sourceUrl": "https://example.com",
            },
            confidence=0.99,
        )
        assert "id" in result

        queue = client.list_review_queue(status="pending")
        ids = [item["id"] for item in queue]
        assert result["id"] in ids
