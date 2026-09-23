"""STEP 03/04/04b: 잡코리아 검색 결과 수집.

- requests(정적 HTML)로 company_name/job_title/career/location/job_url을 파싱한다 (STEP 04 정본).
- Playwright(렌더링 HTML)로 posted_date/closing_date 두 항목만 뽑아 job_id(공고 ID) 기준으로 병합한다 (STEP 04b).
"""

import asyncio
import re
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}
ROBOTS_URL = "https://www.jobkorea.co.kr/robots.txt"
SEARCH_URL_TEMPLATE = "https://www.jobkorea.co.kr/Search/?stext={keyword}"
CARD_SELECTOR = "div.rounded-2xl.shadow-list.bg-white"
DEFAULT_LIMIT = 8
JOB_ID_PATTERN = re.compile(r"GI_Read/(\d+)")


def build_search_url(keyword):
    return SEARCH_URL_TEMPLATE.format(keyword=quote(keyword))


def is_allowed_by_robots(url):
    # STEP 03: robots.txt에서 이 User-Agent로 검색 경로가 허용되는지 확인
    robots_res = requests.get(ROBOTS_URL, headers=HEADERS, timeout=10)
    rp = RobotFileParser()
    rp.set_url(ROBOTS_URL)
    rp.parse(robots_res.text.splitlines())
    return rp.can_fetch(HEADERS["User-Agent"], url)


def fetch_static_html(url):
    # STEP 03: 검색 결과 페이지 1회 요청 (JavaScript 미실행 HTML)
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text


def extract_job(card):
    # STEP 04 셀 코드 기준. career만 전용 셀렉터로 바꿨다 (정적/렌더링 HTML 모두에서 같은 값)
    title_a = card.select_one('a[data-sentry-component="Title"]')
    job_title = title_a.get_text(strip=True) if title_a else None
    job_url = title_a["href"] if title_a else None

    company_span = card.select_one("span.mb-5 a span")
    company_name = company_span.get_text(strip=True) if company_span else None

    location_span = card.select_one('div[data-sentry-component="GrayChip"] span.truncate')
    location = location_span.get_text(strip=True) if location_span else None

    # 경력 span에만 flex-shrink-0이 붙는다. 배지("믿고보는 대기업"), "•", 복리후생, 렌더링된 날짜 span은
    # 같은 text-typo-c1-13 클래스를 쓰기 때문에 "몇 번째 span"으로 고르면 틀릴 수 있다.
    career_span = card.select_one("span.flex-shrink-0.text-typo-c1-13")
    career = career_span.get_text(strip=True) if career_span else None

    return {
        "company_name": company_name,
        "job_title": job_title,
        "career": career,
        "location": location,
        "posted_date": None,  # 정적 HTML에는 없음 → merge_dates()에서 채운다
        "job_url": job_url,
    }


def parse_job_cards(static_html, limit=DEFAULT_LIMIT):
    soup = BeautifulSoup(static_html, "html.parser")
    return [extract_job(card) for card in soup.select(CARD_SELECTOR)[:limit]]


def _fetch_rendered_html_in_thread(url):
    # Jupyter 커널 안에서는 sync API를 바로 못 쓰므로 별도 스레드에서 실행한다.
    # Windows 커널의 기본 이벤트 루프(Selector)는 브라우저 프로세스를 못 띄워서, 이 스레드에서만 Proactor로 바꿨다가 되돌린다.
    old_policy = None
    if sys.platform == "win32":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            old_policy = asyncio.get_event_loop_policy()
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=HEADERS["User-Agent"])
                page.goto(url, timeout=30_000)  # 요청은 이 1회뿐
                page.wait_for_selector(CARD_SELECTOR, timeout=15_000)  # 공고 카드 로드 대기
                page.wait_for_selector(f"{CARD_SELECTOR} >> text=/등록/", timeout=15_000)  # 날짜 렌더링 대기
                return page.content()
            finally:
                browser.close()
    finally:
        if old_policy is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                asyncio.set_event_loop_policy(old_policy)


def fetch_rendered_html(url):
    # STEP 04b: Playwright(headless)로 JavaScript까지 실행된 HTML (스크립트/노트북 어디서든 동작)
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_fetch_rendered_html_in_thread, url).result()


def extract_dates(card):
    # 카드 우측 하단 div: "09/11(금) 등록" / "•" / "09/29(화) 마감" (또는 "상시채용") span이 차례로 들어 있다
    date_area = card.select("div.flex.flex-shrink-0")
    texts = [s.get_text(strip=True) for s in date_area[-1].select("span")] if date_area else []

    posted_date = None
    closing_date = None
    for text in texts:
        if text.endswith("등록"):
            posted_date = text.removesuffix("등록").strip()
        elif text.endswith("마감"):
            closing_date = text.removesuffix("마감").strip()
        elif text != "•":
            closing_date = text  # "상시채용"처럼 날짜가 아닌 마감 표시는 텍스트 그대로
    return posted_date, closing_date


def extract_job_id(job_url):
    # 공고 ID(GI_Read/ 뒤 숫자) - analyzer.add_job_id()와 같은 규칙
    match = JOB_ID_PATTERN.search(job_url or "")
    return match[1] if match else None


def parse_dates_by_job_id(rendered_html):
    # 렌더링 HTML에서는 날짜 두 항목만 뽑는다. job_id는 merge 키로만 쓴다.
    # 정적 요청과 몇 초 차이로 목록 순서가 바뀔 수 있어서 상위 N건이 아니라 페이지의 모든 카드를 본다.
    soup = BeautifulSoup(rendered_html, "html.parser")
    dates_by_job_id = {}
    for card in soup.select(CARD_SELECTOR):
        title_a = card.select_one('a[data-sentry-component="Title"]')
        job_id = extract_job_id(title_a["href"]) if title_a else None
        if job_id is None or job_id in dates_by_job_id:
            continue
        posted_date, closing_date = extract_dates(card)
        dates_by_job_id[job_id] = {"posted_date": posted_date, "closing_date": closing_date}
    return dates_by_job_id


def merge_dates(jobs, dates_by_job_id):
    # job_id를 키로 jobs에 posted_date, closing_date를 추가한다 (jobs를 제자리에서 수정). 매칭 실패 job_url 목록을 돌려준다.
    # job_url 전체는 검색 순번(listno=N)이 요청마다 달라질 수 있어 키로 쓰지 않는다 (GitHub Actions에서 2건 매칭 실패 확인)
    unmatched_urls = []
    for job in jobs:
        dates = dates_by_job_id.get(extract_job_id(job["job_url"]))
        if dates is None:
            unmatched_urls.append(job["job_url"])
            job["posted_date"] = None
            job["closing_date"] = None
        else:
            job["posted_date"] = dates["posted_date"]
            job["closing_date"] = dates["closing_date"]
    return unmatched_urls


def fetch_job_list(keyword, limit=DEFAULT_LIMIT):
    """검색어 하나로 공고 목록(list[dict])을 수집한다. 정적 요청 1회 + Playwright 1회."""
    url = build_search_url(keyword)
    if not is_allowed_by_robots(url):
        raise RuntimeError(f"robots.txt에서 허용되지 않는 경로다: {url}")

    jobs = parse_job_cards(fetch_static_html(url), limit=limit)
    dates_by_job_id = parse_dates_by_job_id(fetch_rendered_html(url))
    unmatched_urls = merge_dates(jobs, dates_by_job_id)
    print(f"[crawler] job_id 매칭 실패 {len(unmatched_urls)}건" + (" (날짜 None으로 둠)" if unmatched_urls else ""))
    return jobs
