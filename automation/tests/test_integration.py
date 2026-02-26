"""End-to-end integration tests (require running backend)."""
import pytest

from fmro_auto.core.api_client import FMROClient
from fmro_auto.core.company_resolver import CompanyResolver


@pytest.fixture
def client():
    with FMROClient() as c:
        yield c


class TestCompanyResolverIntegration:
    def test_creates_and_caches_company(self, client):
        """Verify resolver can create a company via the real backend."""
        resolver = CompanyResolver(client)
        cid = resolver.resolve("IntegrationTest Corp")
        assert cid.isdigit()

        # Second resolve should hit cache, not create again
        cid2 = resolver.resolve("IntegrationTest Corp")
        assert cid == cid2

    def test_finds_existing_company(self, client):
        """Create a company first, then verify resolver finds it."""
        client.create_company(name="ResolverTest Inc")
        resolver = CompanyResolver(client)
        cid = resolver.resolve("ResolverTest Inc")
        assert cid.isdigit()


class TestCreateCompanyAPI:
    def test_create_company(self, client):
        result = client.create_company(name="APITest Co", careers_url="https://example.com/careers")
        assert "id" in result
        assert result["name"] == "APITest Co"

    def test_created_company_in_list(self, client):
        client.create_company(name="ListTest Co")
        companies = client.list_companies()
        names = [c["name"] for c in companies]
        assert "ListTest Co" in names
