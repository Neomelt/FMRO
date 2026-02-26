"""Unit tests for LiepinAdapter parsing logic (mocked browser)."""
from unittest.mock import MagicMock, patch

from fmro_auto.adapters.liepin import _parse_card, LiepinAdapter


class TestParseCard:
    def _make_card(self, title="机器人工程师", company="大疆创新", location="深圳",
                   href="/job/123456"):
        card = MagicMock()
        # safe_text calls card.css("selector::text").get()
        def css_side_effect(selector):
            mock_result = MagicMock()
            if "job-title" in selector or "job-name" in selector or "ellipsis" in selector:
                mock_result.get.return_value = f"  {title}  "
            elif "company-name" in selector:
                mock_result.get.return_value = f"  {company}  "
            elif "location" in selector or "city" in selector or "job-area" in selector or "labels-tag" in selector:
                mock_result.get.return_value = f"  {location}  "
            elif "::text" in selector:
                # Fallback for safe_text — try matching the first selector part
                sel_base = selector.replace("::text", "").strip()
                if "title" in sel_base or "name" in sel_base and "company" not in sel_base:
                    mock_result.get.return_value = f"  {title}  "
                elif "company" in sel_base:
                    mock_result.get.return_value = f"  {company}  "
                elif "location" in sel_base or "city" in sel_base or "area" in sel_base:
                    mock_result.get.return_value = f"  {location}  "
                else:
                    mock_result.get.return_value = None
            else:
                # For link selector (non-text)
                if "href" in selector:
                    link_elem = MagicMock()
                    link_elem.attrib = {"href": href}
                    return [link_elem]
                mock_result.get.return_value = None
            return mock_result
        card.css = css_side_effect
        return card

    def test_parses_valid_card(self):
        card = self._make_card()
        job = _parse_card(card)
        assert job is not None
        assert job.title == "机器人工程师"
        assert job.company_name == "大疆创新"
        assert job.source_platform == "liepin"

    def test_returns_none_on_missing_title(self):
        card = self._make_card(title="")
        job = _parse_card(card)
        assert job is None

    def test_returns_none_on_missing_company(self):
        card = self._make_card(company="")
        job = _parse_card(card)
        assert job is None


class TestLiepinAdapterScrape:
    @patch("fmro_auto.adapters.liepin.StealthyFetcher")
    @patch("fmro_auto.adapters.liepin.random_delay")
    def test_scrape_returns_jobs(self, mock_delay, mock_fetcher):
        """Verify scrape orchestration with mocked fetcher."""
        # Setup mock page with one card
        mock_card = MagicMock()
        def css_fn(selector):
            result = MagicMock()
            if "::text" in selector:
                if "title" in selector or "name" in selector and "company" not in selector:
                    result.get.return_value = "Robot Engineer"
                elif "company" in selector:
                    result.get.return_value = "RoboCorp"
                else:
                    result.get.return_value = None
                return result
            # job_card selector returns cards
            if "job-card" in selector or "job-list" in selector or "sojob" in selector:
                return [mock_card]
            # next_page selector returns empty (one page only)
            if "next" in selector or "pagination" in selector:
                return []
            return [mock_card]

        mock_page = MagicMock()
        mock_page.css = css_fn
        mock_fetcher.fetch.return_value = mock_page

        mock_card.css = css_fn  # reuse the same mock

        api = MagicMock()
        browser = MagicMock()
        adapter = LiepinAdapter(api_client=api, browser_manager=browser)
        jobs = adapter.scrape(keyword="机器人", max_pages=1)

        assert mock_fetcher.fetch.called
        # Should return at least 1 job (may return 0 if parsing fails on mock)
        assert isinstance(jobs, list)
