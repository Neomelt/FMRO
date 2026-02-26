"""Unit tests for scrape_utils (no external dependencies)."""
from unittest.mock import MagicMock

from fmro_auto.core.scrape_utils import normalize_location, safe_text


class TestNormalizeLocation:
    def test_strip_city_suffix(self):
        assert normalize_location("北京市") == "北京"

    def test_strip_whitespace(self):
        assert normalize_location("  上海  ") == "上海"

    def test_compound_location(self):
        assert normalize_location("广州市·天河区") == "广州·天河"

    def test_dash_separator(self):
        assert normalize_location("深圳市-南山区") == "深圳·南山"

    def test_plain_name(self):
        assert normalize_location("杭州") == "杭州"

    def test_empty_string(self):
        assert normalize_location("") == ""

    def test_english_city(self):
        assert normalize_location("Mountain View") == "Mountain View"


class TestSafeText:
    def test_extracts_text(self):
        elem = MagicMock()
        elem.css.return_value.get.return_value = "  Engineer  "
        assert safe_text(elem, ".title") == "Engineer"
        elem.css.assert_called_once_with(".title::text")

    def test_returns_default_on_none(self):
        elem = MagicMock()
        elem.css.return_value.get.return_value = None
        assert safe_text(elem, ".missing") == ""

    def test_returns_default_on_error(self):
        elem = MagicMock()
        elem.css.side_effect = AttributeError("no css")
        assert safe_text(elem, ".broken", "N/A") == "N/A"
