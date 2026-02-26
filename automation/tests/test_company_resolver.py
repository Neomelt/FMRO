"""Unit tests for CompanyResolver with mocked API client."""
from unittest.mock import MagicMock

from fmro_auto.core.company_resolver import CompanyResolver, _normalize_name


class TestNormalizeName:
    def test_strip_suffix(self):
        assert _normalize_name("大疆创新科技有限公司") == "大疆创新"

    def test_strip_multiple_suffixes(self):
        assert _normalize_name("宇树科技集团有限公司") == "宇树"

    def test_lowercase(self):
        assert _normalize_name("Boston Dynamics") == "boston dynamics"

    def test_strip_parens(self):
        assert _normalize_name("优必选（深圳）") == "优必选"

    def test_plain_name(self):
        assert _normalize_name("ABB") == "abb"


class TestCompanyResolver:
    def _make_api(self, companies=None):
        api = MagicMock()
        api.list_companies.return_value = companies or []
        api.create_company.return_value = {"id": 99, "name": "New Co"}
        return api

    def test_finds_existing_company(self):
        api = self._make_api([{"id": 1, "name": "大疆创新科技有限公司"}])
        resolver = CompanyResolver(api)
        assert resolver.resolve("大疆创新") == "1"
        api.create_company.assert_not_called()

    def test_creates_new_company(self):
        api = self._make_api([])
        resolver = CompanyResolver(api)
        assert resolver.resolve("SomeNewCorp") == "99"
        api.create_company.assert_called_once_with(name="SomeNewCorp")

    def test_caches_results(self):
        api = self._make_api([{"id": 5, "name": "宇树科技"}])
        resolver = CompanyResolver(api)
        resolver.resolve("宇树科技")
        resolver.resolve("宇树科技")
        # list_companies should only be called once (cached)
        assert api.list_companies.call_count == 1

    def test_substring_match(self):
        api = self._make_api([{"id": 3, "name": "深圳市大疆创新科技有限公司"}])
        resolver = CompanyResolver(api)
        # "大疆创新" is a substring of normalized "深圳市大疆创新"
        result = resolver.resolve("大疆创新")
        assert result == "3"
        api.create_company.assert_not_called()

    def test_new_company_added_to_cache(self):
        api = self._make_api([])
        resolver = CompanyResolver(api)
        resolver.resolve("TestBot Inc")
        # Second call should use cache, not create again
        api.create_company.return_value = {"id": 100, "name": "should not happen"}
        assert resolver.resolve("TestBot Inc") == "99"
        assert api.create_company.call_count == 1
