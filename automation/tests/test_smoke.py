"""Smoke tests: verify automation infrastructure is wired correctly."""
import subprocess

import httpx

from fmro_auto.core.config import settings


class TestADBConnectivity:
    def test_adb_binary_exists(self):
        result = subprocess.run(["adb", "version"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Android Debug Bridge" in result.stdout

    def test_adb_can_list_devices(self):
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "List of devices attached" in result.stdout


class TestBackendReachable:
    def test_health_endpoint(self):
        resp = httpx.get(f"{settings.fmro_api_base_url}/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") == "true"


class TestPlaywright:
    def test_chromium_launches(self):
        from fmro_auto.core.browser import BrowserManager

        with BrowserManager(headless=True) as mgr:
            page = mgr.new_page()
            page.goto("data:text/html,<h1>FMRO</h1>")
            content = page.content()
            assert "FMRO" in content


class TestApiClient:
    def test_client_health(self):
        from fmro_auto.core.api_client import FMROClient

        with FMROClient() as client:
            data = client.health()
            assert data["ok"] == "true"

    def test_client_list_companies(self):
        from fmro_auto.core.api_client import FMROClient

        with FMROClient() as client:
            companies = client.list_companies()
            assert isinstance(companies, list)


class TestAdapters:
    def test_imports(self):
        from fmro_auto.adapters.boss_zhipin import BossZhipinAdapter
        from fmro_auto.adapters.career_page import CareerPageAdapter
        from fmro_auto.adapters.liepin import LiepinAdapter
        from fmro_auto.adapters.shixiseng import ShixisengAdapter

        assert BossZhipinAdapter.PLATFORM_NAME == "boss_zhipin"
        assert CareerPageAdapter.PLATFORM_NAME == "career_page"
        assert LiepinAdapter.PLATFORM_NAME == "liepin"
        assert ShixisengAdapter.PLATFORM_NAME == "shixiseng"

    def test_scraped_job_payload(self):
        from fmro_auto.adapters.base import ScrapedJob

        job = ScrapedJob(
            company_name="Unitree",
            title="Robotics Intern",
            source_platform="boss_zhipin",
            location="Hangzhou",
        )
        payload = job.to_review_payload()
        assert payload["sourcePlatform"] == "boss_zhipin"
        assert payload["companyName"] == "Unitree"
        assert payload["title"] == "Robotics Intern"
