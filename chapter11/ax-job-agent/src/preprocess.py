"""STEP 05/06: 수집 결과(list[dict])를 DataFrame으로 바꾸고 전처리한다.

- 문자열 컬럼 공백 제거
- 연도 처리 규칙(PROJECT_SPEC.md 10절)으로 posted_date_parsed / closing_date_parsed 추가
- job_url 기준 중복 제거
"""

import re

import pandas as pd

# 알려진 한계: "02/29"가 윤년이 아닌 year로 들어오면 ValueError (PROJECT_SPEC.md 10절)
MMDD_PATTERN = re.compile(r"^(\d{1,2})/(\d{1,2})")


def parse_mmdd(text, year):
    match = MMDD_PATTERN.match(text) if isinstance(text, str) else None
    if match is None:
        return pd.NaT  # "상시채용" 등 날짜 형식이 아닌 값
    return pd.Timestamp(year=year, month=int(match[1]), day=int(match[2]))


def parse_posted_date(text, today):
    posted = parse_mmdd(text, today.year)
    if posted is not pd.NaT and posted > today:  # 등록일은 미래일 수 없다 → 연도 -1
        posted = posted.replace(year=posted.year - 1)
    return posted


def parse_closing_date(text, posted, today):
    # 기준 연도는 '오늘'이 아니라 등록일의 연도 (등록일이 없으면 올해)
    base_year = posted.year if posted is not pd.NaT else today.year
    closing = parse_mmdd(text, base_year)
    if closing is not pd.NaT and posted is not pd.NaT and closing < posted:  # 마감일은 등록일보다 이를 수 없다 → 연도 +1
        closing = closing.replace(year=closing.year + 1)
    return closing


def clean_jobs(jobs, today=None):
    """list[dict] → 전처리된 DataFrame. today(기준일)를 안 주면 오늘 날짜를 쓴다."""
    today = pd.Timestamp.today().normalize() if today is None else pd.Timestamp(today).normalize()
    df = pd.DataFrame(jobs)

    # (1) 모든 문자열 컬럼 앞뒤 공백 제거
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].str.strip()

    # (2) 연도 처리 규칙 - 원본 posted_date/closing_date 문자열은 그대로 두고 새 컬럼에 저장
    posted_parsed = [parse_posted_date(text, today) for text in df["posted_date"]]
    closing_parsed = [
        parse_closing_date(text, posted, today) for text, posted in zip(df["closing_date"], posted_parsed)
    ]
    df["posted_date_parsed"] = pd.to_datetime(pd.Series(posted_parsed, index=df.index))
    df["closing_date_parsed"] = pd.to_datetime(pd.Series(closing_parsed, index=df.index))

    # (3) job_url 기준 중복 제거
    return df.drop_duplicates(subset=["job_url"], keep="first").reset_index(drop=True)
