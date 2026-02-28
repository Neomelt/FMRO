from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "output" / "jobs.csv"
SITE_DIR = ROOT / "site"
SITE_PATH = SITE_DIR / "index.html"


def load_rows() -> list[dict[str, str]]:
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_html(rows: list[dict[str, str]]) -> str:
    trs: list[str] = []
    for row in rows:
        company = esc(row.get("company_name", ""))
        title = esc(row.get("title", ""))
        location = esc(row.get("location", ""))
        platform = esc(row.get("source_platform", ""))
        apply_url = row.get("apply_url", "")
        link = f'<a href="{esc(apply_url)}" target="_blank">投递</a>' if apply_url else "-"
        trs.append(
            f"<tr><td>{company}</td><td>{title}</td><td>{location}</td><td>{platform}</td><td>{link}</td></tr>"
        )

    rows_html = "\n".join(trs) if trs else "<tr><td colspan='5'>暂无岗位数据</td></tr>"

    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>FMRO 机器人岗位看板</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
      margin: 24px;
      background: #0b1220;
      color: #e8eefc;
    }}
    h1 {{ margin: 0 0 12px; }}
    .meta {{ color: #9fb0d9; margin-bottom: 16px; }}
    input {{
      width: 280px;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid #2a3a63;
      background: #101a2e;
      color: #e8eefc;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
      background: #101a2e;
      border-radius: 10px;
      overflow: hidden;
    }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #1f2d4b; text-align: left; }}
    th {{ background: #152342; color: #c7d7ff; }}
    a {{ color: #7db5ff; }}
  </style>
</head>
<body>
  <h1>FMRO 国内机器人岗位</h1>
  <div class=\"meta\">共 {len(rows)} 条（由 GitHub Actions 自动更新）</div>
  <input id=\"q\" placeholder=\"搜索公司/岗位/城市\" />
  <table id=\"jobs\">
    <thead><tr><th>公司</th><th>岗位</th><th>城市</th><th>来源</th><th>链接</th></tr></thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
  <script>
    const q = document.getElementById('q');
    const rows = Array.from(document.querySelectorAll('#jobs tbody tr'));
    q.addEventListener('input', () => {{
      const v = q.value.toLowerCase().trim();
      rows.forEach(r => {{
        r.style.display = r.innerText.toLowerCase().includes(v) ? '' : 'none';
      }});
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    rows = load_rows()
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    SITE_PATH.write_text(build_html(rows), encoding="utf-8")
    print(f"site built: {SITE_PATH}")


if __name__ == "__main__":
    main()
