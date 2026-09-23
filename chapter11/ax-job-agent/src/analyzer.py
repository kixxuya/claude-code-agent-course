"""STEP 07/08: 신규 공고 판별(jobs_history.csv)과 pandas 기본 통계."""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HISTORY_PATH = PROJECT_ROOT / "data" / "processed" / "jobs_history.csv"
DATE_COLUMNS = ["posted_date_parsed", "closing_date_parsed"]


def add_job_id(df):
    # job_url의 GI_Read/ 뒤 숫자(공고 ID). listno 같은 검색 순번 파라미터는 실행마다 바뀌어 키로 못 쓴다.
    df = df.copy()
    df["job_id"] = df["job_url"].str.extract(r"GI_Read/(\d+)", expand=False)
    return df


def load_history(history_path=DEFAULT_HISTORY_PATH):
    history_path = Path(history_path)
    if not history_path.exists():
        return None
    return pd.read_csv(history_path, dtype={"job_id": str}, parse_dates=DATE_COLUMNS)


def detect_new_jobs(df, history_path=DEFAULT_HISTORY_PATH):
    """job_id를 붙이고 history와 비교해 is_new 컬럼을 추가한다. 파일은 쓰지 않는다 (update_history 참고)."""
    df = add_job_id(df)
    history = load_history(history_path)
    known_ids = set(history["job_id"].dropna()) if history is not None else set()
    # job_id가 NaN인 행은 비교할 수 없으므로 신규로 치지 않는다
    df["is_new"] = df["job_id"].notna() & ~df["job_id"].isin(known_ids)
    return df


def update_history(df, history_path=DEFAULT_HISTORY_PATH):
    """is_new=True인 행만 history 뒤에 붙여 저장한다 (같은 job_id가 있으면 기존 행 유지). 저장 후 행 수를 돌려준다."""
    history_path = Path(history_path)
    history = load_history(history_path)
    new_rows = df[df["is_new"]]
    if history is not None and len(history):
        updated = pd.concat([history, new_rows], ignore_index=True)
    else:
        updated = new_rows.reset_index(drop=True)
    updated = updated.drop_duplicates(subset=["job_id"], keep="first")

    history_path.parent.mkdir(parents=True, exist_ok=True)
    updated.to_csv(history_path, index=False, encoding="utf-8-sig")
    return len(updated)


def summarize_stats(df_new, today=None, top_n=5):
    """신규 공고 DataFrame의 pandas 통계 (Gemini 미사용, PROJECT_SPEC.md 원칙 7)."""
    today = pd.Timestamp.today().normalize() if today is None else pd.Timestamp(today).normalize()

    has_deadline = df_new.dropna(subset=["closing_date_parsed"])
    closing_soon = has_deadline.sort_values("closing_date_parsed").head(top_n).copy()
    closing_soon["days_left"] = (closing_soon["closing_date_parsed"] - today).dt.days
    no_deadline = df_new[df_new["closing_date_parsed"].isna()]

    return {
        "new_count": len(df_new),
        "career_counts": df_new["career"].value_counts(dropna=False).to_dict(),
        "location_counts": df_new["location"].value_counts(dropna=False).to_dict(),
        "closing_soon": closing_soon[["company_name", "job_title", "closing_date_parsed", "days_left"]].reset_index(drop=True),
        "no_deadline_count": len(no_deadline),
        "no_deadline_texts": no_deadline["closing_date"].tolist(),
    }
