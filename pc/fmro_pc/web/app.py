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
DB_PATH = ROOT_DIR / "data" / "fmro_pc.db"


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
        f"抓取完成：源={summary.source_count}，页面={summary.total_pages_fetched}，"
        f"抽取={summary.total_jobs_extracted}，新增={summary.total_jobs_inserted}，"
        f"更新={summary.total_jobs_updated}，失败={summary.total_failures}"
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
    st.set_page_config(page_title="FMRO 机器人岗位", page_icon="🤖", layout="wide")
    st.title("FMRO 国内机器人岗位")

    if not CONFIG_PATH.exists():
        st.error(f"缺少配置文件: {CONFIG_PATH}")
        return

    config = load_companies_config(CONFIG_PATH)

    with st.sidebar:
        st.header("抓取")
        source_options = ["全部"] + [s.key for s in config.sources if s.enabled]
        selected_source = st.selectbox("数据源", source_options)
        force_dynamic = st.checkbox("强制动态渲染", value=False)
        if st.button("开始抓取", type="primary"):
            with st.spinner("抓取中..."):
                try:
                    source_key = None if selected_source == "全部" else selected_source
                    message = _run_crawl(source_key, force_dynamic)
                    st.success(message)
                except Exception as exc:  # noqa: BLE001
                    st.error(str(exc))

        st.divider()
        st.header("导出")
        if st.button("导出 CSV"):
            out = ROOT_DIR / "output" / "jobs.csv"
            with session_scope(DB_PATH) as session:
                count = export_jobs_csv(session, out)
            st.info(f"已导出 {count} 条到 {out}")

        if st.button("导出 Markdown"):
            out = ROOT_DIR / "output" / "jobs.md"
            with session_scope(DB_PATH) as session:
                count = export_jobs_markdown(session, out)
            st.info(f"已导出 {count} 条到 {out}")

    col1, col2, col3, col4 = st.columns(4)
    keyword = col1.text_input("关键词", value="机器人")
    city = col2.text_input("城市")
    platform = col3.text_input("来源平台")
    unapplied = col4.checkbox("仅看未投递", value=True)

    jobs = _load_jobs(keyword, city, platform, unapplied)
    st.caption(f"当前共 {len(jobs)} 条岗位")

    for job in jobs:
        with st.expander(f"[{job.id}] {job.company_name} - {job.title}"):
            st.write(f"地点: {job.location or '-'}")
            st.write(f"平台: {job.source_platform}")
            st.write(f"投递链接: {job.apply_url}")
            st.write(f"来源链接: {job.source_url}")
            st.write(f"已投递: {'是' if job.applied else '否'}")
            st.write(f"已收藏: {'是' if job.bookmarked else '否'}")

            b1, b2, b3 = st.columns(3)
            if b1.button("标记已投递", key=f"apply-{job.id}"):
                with session_scope(DB_PATH) as session:
                    mark_applied(session, job_id=job.id)
                st.rerun()

            if b2.button(
                "取消收藏" if job.bookmarked else "收藏",
                key=f"bookmark-{job.id}",
            ):
                with session_scope(DB_PATH) as session:
                    set_bookmark(session, job_id=job.id, enabled=not job.bookmarked)
                st.rerun()

            note_value = st.text_area("备注", value=job.notes or "", key=f"note-{job.id}")
            if b3.button("保存备注", key=f"save-note-{job.id}"):
                with session_scope(DB_PATH) as session:
                    set_note(session, job_id=job.id, text=note_value)
                st.rerun()


if __name__ == "__main__":
    main()
