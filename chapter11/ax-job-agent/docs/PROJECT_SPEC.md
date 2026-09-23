# AX 채용정보 Agent Pipeline — 프로젝트 사양

> Chapter 11 실습 (AI Agent Engineering) · 브랜치: `ax-job-agent`
> 이 문서는 프로젝트의 "고정 사양"입니다. 진행 상황은 `PROGRESS.md`에서 관리합니다.

---

## 1. 목표

잡코리아의 AX / AI / 데이터 분석 관련 채용공고를 **주 1회 자동으로 수집·분석·요약**해서
Slack과 Gmail로 보고서를 보내는 작은 Agent Pipeline을 만든다.

핵심은 크롤링 기술이 아니라 **수집 → 정제 → 분석 → AI 해석 → 검증 → 보고 → 자동화**가
하나의 파이프라인으로 연결되는 과정을 이해하는 것.

---

## 2. 시스템 구조

### 개발 단계

```
웹 LLM (Orchestrator)
    ↓ 계획 / STEP 프롬프트
Claude Code (Coding Agent, VS Code)
    ↓ 코드 작성
Jupyter Notebook
    ↓ 셀 단위 실행 / 결과 확인 (Human Verification)
main.py 완성
```

### 운영 단계

```
GitHub Actions (주 1회, cron)
    ↓
main.py
    ↓
Crawler → pandas(정제/중복제거/신규판별/필터/통계) → Gemini API(요약/추천) → Report(Markdown)
    ↓
Slack / Gmail
```

### 역할 구분

| 주체 | 역할 |
|---|---|
| 웹 LLM (GPT/Gemini/Claude Web) | 개발 전체를 계획하는 Orchestrator |
| Claude Code | 프로젝트 파일과 코드를 다루는 Coding Agent |
| Gemini API | 운영 파이프라인 내부에서 채용공고를 요약하는 AI |
| GitHub Actions | 주기적으로 main.py를 실행하는 Scheduler |
| 사람(희주) | 목표와 검증 기준을 관리하는 최종 승인자 |

---

## 3. 데이터 명세

**DataFrame의 한 행 = 채용공고 한 건**

| 컬럼명 | 의미 |
|---|---|
| company_name | 회사명 |
| job_title | 공고 제목 |
| career | 경력 조건 |
| location | 근무 지역 |
| posted_date | 등록일 |
| closing_date | 마감일 |
| job_url | 공고 URL (신규/중복 판별 기준 키) |
| search_keyword | 어떤 검색어로 발견했는지 |
| collected_at | 수집 시각 |

**신규 공고 판별 기준**: `job_url` 기준. 보조 키가 필요하면 `회사명 + 공고 제목 + 마감일` 조합 사용.
히스토리 저장: `data/processed/jobs_history.csv`

---

## 4. 폴더 구조

```
chapter11/ax-job-agent/
├── .venv/                      (이 프로젝트 전용 가상환경, git 추적 안 함)
├── docs/
│   ├── PROJECT_SPEC.md         (이 문서)
│   └── PROGRESS.md             (진행 상황 추적)
├── notebooks/
│   └── ax_job_pipeline.ipynb   (STEP별 검증 기록)
├── src/
│   ├── crawler.py
│   ├── preprocess.py
│   ├── analyzer.py
│   ├── gemini_client.py
│   ├── reporter.py
│   └── notifier.py
├── data/
│   ├── raw/
│   └── processed/
├── reports/
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

처음부터 전부 만들지 않는다. 필요해질 때 STEP별로 하나씩 추가한다.

---

## 5. STEP 목록 (전체 18단계)

| STEP | 내용 |
|---|---|
| 01 | 개발환경 확인 |
| 02 | 수집 데이터 명세 |
| 03 | 채용공고 페이지 접근 테스트 |
| 04 | 소량 데이터 수집 |
| 05 | DataFrame 생성 |
| 06 | 전처리 / 중복 제거 |
| 07 | 신규 공고 판별 |
| 08 | 기본 분석 / 관련 공고 필터링 |
| 09 | Gemini API 연동 |
| 10 | Gemini 결과 검증 |
| 11 | Markdown 보고서 생성 |
| 12 | Slack 발송 |
| 13 | Gmail 발송 |
| 14 | 함수화 (src/로 이동) |
| 15 | main.py 통합 |
| 16 | 로컬 전체 실행 검증 |
| 17 | GitHub Actions 수동 실행 |
| 18 | GitHub Actions 주간 실행 (cron) |

---

## 6. 지켜야 할 원칙 (10가지)

1. 한 번에 전체 프로그램을 만들지 않는다.
2. 현재 STEP 하나만 Claude Code에 맡긴다.
3. 코드가 생성되면 직접 실행한다.
4. 실행 결과를 눈으로 확인한다.
5. 결과를 Markdown으로 해석한다 (Notebook에 기록).
6. 이상하면 다음 단계로 넘어가지 않는다.
7. 계산 가능한 사실(건수, 통계 등)은 pandas로 계산한다. Gemini에게 맡기지 않는다.
8. Gemini는 요약·해석 중심으로만 사용한다.
9. API Key와 비밀번호는 절대 Git에 올리지 않는다 (.env / GitHub Secrets 사용).
10. 로컬 검증(`python main.py` 성공)이 끝난 뒤에만 GitHub Actions를 추가한다.

---

## 7. 환경 정보

- 가상환경: `chapter11/ax-job-agent/.venv` (프로젝트 전용, 루트 `.venv`와 별개)
- 초기 패키지: `pandas`, `requests`, `beautifulsoup4`, `jupyter`, `python-dotenv`
- 아직 설치하지 않음: Gemini SDK, Slack/Gmail 관련 패키지 (필요한 STEP에서 추가)
- 브랜치: `ax-job-agent` (origin = 본인 Fork, upstream = GilbertMoon/claude-code-agent-course)

---

## 8. Notebook 셀 작성 패턴 (모든 STEP 공통)

```
[Markdown Cell] # STEP xx. 제목
                ## 작업 계획
                (이번 단계에서 확인할 것)

[Code Cell]     # 실행 코드

[Code Cell]     # 결과 확인 (shape, head, status code 등)

[Markdown Cell] ## 실행 결과 해석
                - 성공 여부:
                - 확인한 데이터:
                - 예상과 다른 부분:
                - 다음 단계 진행 가능 여부:
                - 추가 확인 사항:
```

---

## 9. 크롤링 정책 및 판단 근거 (STEP 03에서 확인)

**확인된 사실 (2026-09-23):**
- 잡코리아 robots.txt는 `GPTBot`, `ClaudeBot`, `anthropic-ai`, `Claude-Web` 등 AI 크롤러 User-Agent를 이름으로 지정해 전면 차단(`Disallow: /`)하고 있음.
- 일반 브라우저 User-Agent(`Mozilla/5.0 ... Chrome/120.0`)에 적용되는 `User-agent: *` 규칙에서는 `/Search/` 경로가 막혀있지 않음.
- 검색 페이지 요청은 status_code 200, 실제 채용공고 텍스트 확인됨.

**판단 (사람이 직접 검토하고 결정함):**
- 브라우저 UA로 요청을 계속 진행하기로 결정함 (소량·저빈도, 주 1회 실행 목적).
- 다만 이 사이트가 AI 자동 접근을 명시적으로 원하지 않는다는 신호가 있다는 점은 인지하고 있음.

**앞으로 지키는 것:**
- User-Agent에 "Claude", "anthropic", "GPT" 등 AI 식별자를 넣지 않는다 (이미 지키고 있음, 다만 우회 목적이 아니라 일반 브라우저 UA를 사실대로 사용).
- 요청 빈도를 최소화한다 (주 1회, 필요한 만큼만).
- 수집한 데이터는 개인 학습·모니터링 용도로만 사용하고 재배포하지 않는다.
- 사이트 운영 정책이 바뀌거나 차단이 강화되면 즉시 수집을 중단하고 이 문서를 갱신한다.

---

## 10. posted_date 수집 방식 결정 (STEP 04 → 변경, 2026-09-23)

**확인된 사실:**
- 브라우저 화면에는 각 공고 우측 하단에 "09/11(금) 등록 • 09/29(화) 마감" 형태의 날짜가 보임.
- `requests`로 받아온 정적 HTML에는 그 위치의 `div`가 **비어있음** — 이 날짜는 페이지 로드 후 **자바스크립트가 채워 넣는 클라이언트 렌더링 데이터**라서 `requests`(자바스크립트 미실행)로는 못 가져옴.

**최초 결정 (1차)**: posted_date 없이 진행 → **번복함**. 사람(희주)이 "등록일이 화면에 보이니 반드시 넣어야 한다"고 재결정함.

**최종 결정 (2차, 현재 유효):**
- **Playwright**(브라우저 자동화, 자바스크립트 실행 가능)를 추가로 설치해서 실제 렌더링된 화면의 텍스트를 읽어 posted_date를 채운다.
- STEP 03/04에서 쓰던 `requests` 기반 수집은 유지하되(가볍고 빠름), posted_date만 Playwright로 보강하는 방식을 우선 시도한다. 안 되면 전체 수집을 Playwright로 전환한다.
- GitHub Actions(운영 환경)에서도 Playwright는 headless Chromium으로 정상 동작하므로 자동화 단계(STEP 17~18)에서도 문제 없음.

**환경 변경 사항:**
- 신규 패키지: `playwright` (설치 후 `python -m playwright install chromium` 별도 실행 필요)

**방침 수정 (2026-09-23, 최종):**
- STEP 04(requests 기반)의 company_name/job_title/career/location/job_url 파싱 결과는
  그대로 정본으로 유지한다. 이 항목들은 이미 정확하게 확인됨.
- Playwright는 posted_date, closing_date **딱 두 항목만** 추출하는 용도로 좁혀서 쓴다.
- 두 결과를 job_url 기준으로 병합(merge)해서, 최종 변수명은 `jobs`로 유지한다.
  (`jobs_rendered`라는 별도 변수를 이후 STEP에 넘기지 않는다)
- 이유: 이미 검증된 파싱 로직을 불필요하게 재작성하지 않기 위해서.

**연도 처리 규칙 (STEP 06에서 적용):**
- posted_date, closing_date는 MM/DD(요일) 형식이라 연도가 없다.
- posted_date는 미래일 수 없다 → 현재 연도로 계산한 날짜가 오늘보다 미래면 연도 -1.
- closing_date는 posted_date보다 과거일 수 없다 → posted_date_parsed와 같은 연도로 계산한
  closing_date가 posted_date_parsed보다 이르면 연도 +1 (기준은 '오늘'이 아니라
  posted_date_parsed의 연도).
- "상시채용" 등 날짜 형식이 아닌 값은 파싱하지 않고 원문 텍스트 그대로 저장한다 (연도 계산 대상 아님).
- 알려진 한계: "02/29"가 윤년이 아닌 연도로 계산되면 날짜 생성 에러가 난다. 드문 경우라 현재는 예외 처리하지 않는다.
