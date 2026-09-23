"""STEP 09/10: .env 로드, Gemini client, 공고 한 줄 요약.

API 키는 .env(환경변수 GEMINI_API_KEY)에서만 읽고, 코드에 쓰거나 출력하지 않는다.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 프로젝트 폴더(.env.example 옆)를 먼저 찾고, 없으면 상위 chapter11 폴더의 .env를 쓴다
ENV_CANDIDATES = [PROJECT_ROOT / ".env", PROJECT_ROOT.parent / ".env"]
GEMINI_MODEL = "gemini-3.5-flash-lite"
SLEEP_SECONDS = 1.0  # 여러 건 요약 시 API 호출 사이 간격

_client = None


def load_env():
    """.env를 찾아 환경변수로 로드한다. 찾은 파일 경로(없으면 None)를 돌려준다."""
    env_path = next((path for path in ENV_CANDIDATES if path.exists()), None)
    if env_path is not None:
        load_dotenv(env_path)
    return env_path


def get_client():
    global _client
    if _client is None:
        from google import genai

        load_env()
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("GEMINI_API_KEY가 없다. .env.example을 복사해서 .env를 만들고 키를 넣는다.")
        _client = genai.Client()  # 환경변수 GEMINI_API_KEY를 자동으로 읽는다
    return _client


def build_job_text(job):
    return (
        f"회사명: {job['company_name']}\n"
        f"공고 제목: {job['job_title']}\n"
        f"경력 조건: {job['career']}"
    )


def summarize_job(job, model=GEMINI_MODEL):
    """공고 1건(dict 또는 Series)을 한국어 한 문장으로 요약한다 (STEP 09/10과 같은 프롬프트)."""
    prompt = (
        "다음 채용공고를 한국어 한 문장(50자 이내)으로 요약해줘. "
        "주어진 정보에 없는 내용은 추측해서 덧붙이지 마.\n\n" + build_job_text(job)
    )
    response = get_client().models.generate_content(model=model, contents=prompt)
    return response.text.strip()


def summarize_jobs(df, model=GEMINI_MODEL, sleep_seconds=SLEEP_SECONDS):
    """DataFrame의 공고를 한 건씩 요약한다. 실패한 건은 None으로 두고 계속 진행한다."""
    summaries = []
    for i, (_, job) in enumerate(df.iterrows(), start=1):
        try:
            summaries.append(summarize_job(job, model=model))
        except Exception as e:  # 한 건이 실패해도 나머지는 계속 진행
            summaries.append(None)
            print(f"[gemini] {i}/{len(df)} 실패: {job['company_name']} ({type(e).__name__})")
        if i < len(df):
            time.sleep(sleep_seconds)
    return summaries
