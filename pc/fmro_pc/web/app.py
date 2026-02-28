from __future__ import annotations

from pathlib import Path

import streamlit as st

from fmro_pc.config import load_companies_config
from fmro_pc.crawl.runner import run_crawl
from fmro_pc.database import init_db, session_scope
from fmro_pc.services.jobs import mark_applied, query_jobs, set_bookmark, set_note
from fmro_pc.storage.repository import export_jobs_csv, export_jobs_markdown

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "companies.yaml"
DB_PATH = ROOT_DIR / "fmro_pc.db"


def _run_crawl(source_key: str | None, force_dynamic: bool) -> str:
    config = load_companies_config(CONFIG_PATH)
    init_db(DB_PATH)
    with session_scope(DB_PATH) as session:
        summary = run_crawl(
            session,
            config,
            source_key=source_key or None,
            force_dynamic=force_dynamic,
        )
    return (
        f"Done. sources={summary.source_count}, pages={summary.total_pages_fetched}, "
        f"extracted={summary.total_jobs_extracted}, inserted={summary.total_jobs_inserted}, "
        f"updated={summary.total_jobs_updated}, failures={summary.total_failures}"
    )


def _load_jobs(keyword: str, city: str, platform: str, unapplied: bool) -> list:
    init_db(DB_PATH)
    with session_scope(DB_PATH) as session:
        return query_jobs(
            session,
            keyword=keyword or None,
            city=city or None,
            platform=platform or None,
            unapplied=unapplied,
            include_inactive=False,
            sort="updated_at",
            limit=500,
        )


def main() -> None:
    st.set_page_config(page_title="FMRO Jobs", page_icon="🤖", layout="wide")
    st.title("FMRO Robotics Jobs")

    if not CONFIG_PATH.exists():
        st.error(f"Missing config: {CONFIG_PATH}")
        return

    config = load_companies_config(CONFIG_PATH)

    with st.sidebar:
        st.header("Crawl")
        source_options = [""] + [s.key for s in config.sources if s.enabled]
        selected_source = st.selectbox("Source (empty = all)", source_options)
        force_dynamic = st.checkbox("Force dynamic", value=False)
        if st.button("Run Crawl", type="primary"):
            with st.spinner("Crawling..."):
                try:
                    message = _run_crawl(selected_source, force_dynamic)
                    st.success(message)
                except Exception as exc:  # noqa: BLE001
                    st.error(str(exc))

        st.divider()
        st.header("Export")
        if st.button("Export CSV"):
            out = ROOT_DIR / "output" / "jobs.csv"
            with session_scope(DB_PATH) as session:
                count = export_jobs_csv(session, out)
            st.info(f"Exported {count} jobs to {out}")

        if st.button("Export Markdown"):
            out = ROOT_DIR / "output" / "jobs.md"
            with session_scope(DB_PATH) as session:
                count = export_jobs_markdown(session, out)
            st.info(f"Exported {count} jobs to {out}")

    col1, col2, col3, col4 = st.columns(4)
    keyword = col1.text_input("Keyword")
    city = col2.text_input("City")
    platform = col3.text_input("Platform")
    unapplied = col4.checkbox("Unapplied only", value=False)

    jobs = _load_jobs(keyword, city, platform, unapplied)
    st.caption(f"{len(jobs)} jobs")

    for job in jobs:
        with st.expander(f"[{job.id}] {job.company_name} - {job.title}"):
            st.write(f"Location: {job.location or '-'}")
            st.write(f"Platform: {job.source_platform}")
            st.write(f"Apply: {job.apply_url}")
            st.write(f"Source: {job.source_url}")
            st.write(f"Applied: {'yes' if job.applied else 'no'}")
            st.write(f"Bookmarked: {'yes' if job.bookmarked else 'no'}")

            b1, b2, b3 = st.columns(3)
            if b1.button("Mark Applied", key=f"apply-{job.id}"):
                with session_scope(DB_PATH) as session:
                    mark_applied(session, job_id=job.id)
                st.rerun()

            if b2.button(
                "Unbookmark" if job.bookmarked else "Bookmark",
                key=f"bookmark-{job.id}",
            ):
                with session_scope(DB_PATH) as session:
                    set_bookmark(session, job_id=job.id, enabled=not job.bookmarked)
                st.rerun()

            note_value = st.text_area("Note", value=job.notes or "", key=f"note-{job.id}")
            if b3.button("Save Note", key=f"save-note-{job.id}"):
                with session_scope(DB_PATH) as session:
                    set_note(session, job_id=job.id, text=note_value)
                st.rerun()


if __name__ == "__main__":
    main()
