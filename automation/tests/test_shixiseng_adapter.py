"""Unit tests for ShixisengAdapter parsing logic (mocked browser)."""
from unittest.mock import MagicMock, patch

from fmro_auto.adapters.shixiseng import _parse_card, ShixisengAdapter


class TestParseCard:
    def _make_card(self, title="机器人实习生", company="宇树科技", location="杭州市",
                   href="/intern/abc123"):
        card = MagicMock()
        def css_fn(selector):
            result = MagicMock()
            if "::text" in selector:
                if "title" in selector or "position" in selector or "job-name" in selector:
                    result.get.return_value = f"  {title}  "
                elif "company" in selector:
                    result.get.return_value = f"  {company}  "
                elif "city" in selector or "address" in selector:
                    result.get.return_value = f"  {location}  "
                else:
                    result.get.return_value = None
                return result
            if "href" in selector:
                link = MagicMock()
                link.attrib = {"href": href}
                return [link]
            return result
        card.css = css_fn
        return card

    def test_parses_valid_card(self):
        card = self._make_card()
        job = _parse_card(card)
        assert job is not None
        assert job.title == "机器人实习生"
        assert job.company_name == "宇树科技"
        assert job.source_platform == "shixiseng"
        assert job.location == "杭州"  # normalized: 杭州市 -> 杭州

    def test_returns_none_on_empty_title(self):
        card = self._make_card(title="")
        job = _parse_card(card)
        assert job is None


class TestShixisengAdapterScrape:
    @patch("scrapling.fetchers.StealthyFetcher")
    @patch("fmro_auto.adapters.shixiseng.random_delay")
    def test_scrape_basic_flow(self, mock_delay, mock_fetcher):
        mock_card = MagicMock()
        def css_fn(selector):
            result = MagicMock()
            if "::text" in selector:
                if "title" in selector or "position" in selector or "job-name" in selector:
                    result.get.return_value = "Robot Intern"
                elif "company" in selector:
                    result.get.return_value = "InternCorp"
                else:
                    result.get.return_value = None
                return result
            if "intern" in selector:
                return [mock_card]
            if "next" in selector or "pagination" in selector:
                return []
            return [mock_card]

        mock_page = MagicMock()
        mock_page.css = css_fn
        mock_fetcher.fetch.return_value = mock_page
        mock_card.css = css_fn

        api = MagicMock()
        browser = MagicMock()
        adapter = ShixisengAdapter(api_client=api, browser_manager=browser)
        jobs = adapter.scrape(keyword="机器人", max_pages=1)

        assert mock_fetcher.fetch.called
        assert isinstance(jobs, list)
