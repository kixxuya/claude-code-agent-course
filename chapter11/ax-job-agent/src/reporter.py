"""STEP 11: 요약 결과로 Markdown 보고서를 만들고 reports/YYYY-MM-DD.md로 저장한다."""

from pathlib import Path

import pandas as pd

from src.gemini_client import GEMINI_MODEL

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"


def format_closing(row, report_date):
    if pd.isna(row["closing_date_parsed"]):
        return row["closing_date"]  # "상시채용" 등 원문 그대로
    days_left = (row["closing_date_parsed"] - report_date).days
    if days_left > 0:
        d_day = f"D-{days_left}"
    elif days_left == 0:
        d_day = "D-day"
    else:
        d_day = "마감 지남"
    return f"{row['closing_date_parsed']:%Y-%m-%d} ({d_day})"


def build_report_markdown(df_summary, report_date=None, model=GEMINI_MODEL):
    """df_summary 필요 컬럼: company_name, job_title, career, location, closing_date, closing_date_parsed,
    job_url, gemini_summary. 마감 임박 순(마감일 없는 공고는 맨 뒤)으로 정렬한다."""
    report_date = pd.Timestamp.today().normalize() if report_date is None else pd.Timestamp(report_date).normalize()
    report_df = df_summary.sort_values("closing_date_parsed", na_position="last").reset_index(drop=True)

    lines = [
        "# AX 채용정보 주간 리포트",
        "",
        f"- 생성일: {report_date:%Y-%m-%d}",
        f"- 신규 공고 건수: {len(report_df)}건",
        f"- 요약 모델: {model}",
        "- 정렬: 마감 임박 순 (마감일 없는 공고는 맨 뒤)",
        "",
        "---",
        "",
    ]
    for i, row in report_df.iterrows():
        lines += [
            f"## {i + 1}. {row['company_name']} — {row['job_title']}",
            "",
            f"- 경력: {row['career']}",
            f"- 지역: {row['location']}",
            f"- 마감일: {format_closing(row, report_date)}",
            f"- 요약 (Gemini): {row['gemini_summary']}",
            f"- 공고 링크: {row['job_url']}",
            "",
        ]
    return "\n".join(lines)


def default_report_path(report_date=None):
    report_date = pd.Timestamp.today() if report_date is None else pd.Timestamp(report_date)
    return REPORTS_DIR / f"{report_date:%Y-%m-%d}.md"


def save_report(markdown, path=None):
    """보고서를 저장하고 경로를 돌려준다. path를 안 주면 reports/오늘날짜.md (같은 날이면 덮어씀)."""
    path = default_report_path() if path is None else Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path
