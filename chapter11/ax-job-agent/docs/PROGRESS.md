# 진행 상황 추적 (PROGRESS)

> 매번 작업 시작 전 이 파일을 먼저 확인한다.
> 상태 표시: `[ ]` 미시작 · `[~]` 진행 중 · `[x]` 완료

---

## 현재 상태 (마지막 업데이트: 2026-09-23)

- **완료된 마지막 STEP**: STEP 18 (GitHub Actions 주간 실행) — 매주 월요일 09:00 KST(UTC `0 0 * * 1`) cron 추가, main에서 active 확인. 전체 18단계 구현 완료
- **지금 하고 있는 것**: 없음 (첫 자동 실행 대기)
- **다음에 할 일**: **첫 자동 실행 결과 확인 — 2026-09-28(월) 09:00 KST 예정** (GitHub 부하에 따라 몇 분~수십 분 늦게 시작될 수 있음)
  - 확인할 것: Actions 실행 성공 여부, job_id 매칭 실패 건수, 신규 건수. 신규가 있으면 Gemini 요약·보고서·Gmail·Slack 발송과 `github-actions[bot]`의 jobs_history.csv 커밋(main 브랜치)까지.
  - 참고: 지금까지 실제 실행(run 35836468808 등)은 모두 신규 0건이라 발송·history 커밋이 없었다. STEP 16에서 결정한 대로, 신규 공고가 실제로 나타나는 주간 실행에서 전체 발송 경로가 자연스럽게 검증될 예정이다.
  - 주의: 스케줄 실행은 main에서 돌고 봇 커밋도 main에 쌓인다. ax-job-agent 브랜치에서 작업을 이어가기 전에 `git pull origin main`으로 main의 봇 커밋을 먼저 받아온다.
  - 주의: 저장소에 60일 동안 활동이 없으면 GitHub가 스케줄 실행을 자동으로 비활성화한다.
- **막힌 부분 / 확인 필요**: 없음

> ⚠️ 작업할 때마다 이 섹션(현재 상태)을 직접 갱신할 것. Claude Code에게 "PROGRESS.md 업데이트해줘"라고 요청해도 됨.

---

## 사전 준비 체크리스트

- [x] PUBLIC 저장소 Fork (`kixxuya/claude-code-agent-course`)
- [x] 로컬 Clone (`C:\dev\claude-code-agent-course`)
- [x] upstream 원격 저장소 연결
- [x] 실습 브랜치 생성 (`ax-job-agent`)
- [x] 프로젝트 폴더 생성 (`chapter11/ax-job-agent`)
- [x] 프로젝트 전용 가상환경 생성 및 활성화 (`chapter11/ax-job-agent/.venv`)
- [x] 초기 패키지 설치 확인 (pandas, requests, beautifulsoup4, jupyter, python-dotenv)

---

## STEP 체크리스트

### 개발 단계

- [x] STEP 01. 개발환경 확인 — notebook 생성, 전용 커널 등록, 셀 실행 확인
- [x] STEP 02. 수집 데이터 명세 확정 — PROJECT_SPEC.md 3절에 컬럼 정의 완료
- [x] STEP 03. 채용공고 페이지 접근 테스트 — status_code 200, 검색결과 885건 확인, robots.txt 판단 근거 기록(PROJECT_SPEC.md 9절)
- [x] STEP 04. 소량 데이터 수집 (1개 검색어, 5~10개 공고) — requests + BeautifulSoup로 8건 수집. company_name/job_title/career/location/job_url 정본
- [x] STEP 04b. posted_date, closing_date 보강 (신규) — Playwright(headless) 렌더링 HTML에서 날짜 두 항목만 추출해 job_url 기준으로 jobs에 병합, 매칭 실패 0건 (PROJECT_SPEC.md 10절)
- [x] STEP 05. DataFrame 생성 — df.shape (8,7), 전체 컬럼 결측 0건, job_url 중복 0건
- [x] STEP 06. 전처리 / 중복 제거 — 문자열 strip, 연도 처리 규칙으로 posted_date_parsed/closing_date_parsed 추가, job_url 기준 중복 제거 (8→8행)
- [x] STEP 07. 신규 공고 판별 (jobs_history.csv 기준) — job_id(공고 ID) 기준 비교, data/processed/jobs_history.csv 신규 생성 (8건 전부 신규)
- [x] STEP 08. 기본 분석 / 관련 공고 필터링 (pandas 통계) — 신규 공고(is_new=True) 8건 대상 career/location 분포, 마감 임박 상위 5건, 마감일 없는 공고 1건
- [x] STEP 09. Gemini API 연동 (.env, .env.example, .gitignore 설정 포함) — google-genai 2.25.0, gemini-3.5-flash-lite로 공고 1건 한 줄 요약 성공
- [x] STEP 10. Gemini 결과 검증 (원문 대조) — 8/8 요약, 사람 대조: 사실 오류 0, 지어낸 내용 0, 직무 누락 1(경미)
- [x] STEP 11. Markdown 보고서 생성 — reports/2026-09-23.md (72줄, 3545 bytes, 8건, 마감 임박 순, 요약 모델명 기재)
- [x] STEP 12. Slack 발송 — 보류 해제, src/notifier.py의 send_slack()으로 실제 발송 성공 (HTTP 200), 팀스파르타 AX 2기 워크스페이스에서 수신 확인: 8건 전체 반영, 마크다운 기호는 Slack 특성상 텍스트 그대로 표시
- [x] STEP 13. Gmail 발송 — smtplib + smtp.gmail.com:587(STARTTLS), 본인에게 1건 테스트 발송·수신 확인 (본문 + .md 첨부)
- [x] STEP 14. 함수화 (src/ 로 이동) — src/ 6개 모듈, 노트북 검증값과 30/30 일치. fetch_job_list/summarize_job 로직은 STEP 04/09/10에서, send_gmail/send_slack 로직은 STEP 13/12에서 이미 실제 호출로 검증됨 → 개별 재호출 테스트(STEP 14-1)는 중복이라 생략
- [x] STEP 15. main.py 통합 — dry-run/실제 모드 둘 다 실행 성공, 신규 0건 케이스에서 안전하게 종료 확인, 실행 모드 로그 정상
- [x] STEP 16. 로컬 전체 실행 검증 (`python main.py`) — 실제 실행 성공. '신규 있음' 전체 흐름(Gemini→보고서→발송→history)은 개별 로직의 실제 호출 검증(STEP 04/09/10 노트북, STEP 12 src send_slack, STEP 13 노트북 send_gmail) + STEP 14 리팩토링 30/30 값 일치 + main.py 모의 테스트(A~D 케이스)로 커버됐다고 판단, 강제 재현은 생략. 다음에 실제 신규 공고가 뜨는 주에 자연스럽게 end-to-end 검증됨

### 배포 단계

- [x] Git 커밋 (민감정보 미포함 확인 후) — 6c59eb5, 17개 파일 명시적 add, 민감정보 grep 8개 항목 모두 없음
- [x] origin(내 Fork)로 push — `ax-job-agent` 브랜치 신규 생성, upstream 설정
- [x] STEP 17. GitHub Actions 수동 실행 (workflow_dispatch) — dry_run·실제 실행 모두 성공 (job_id 매칭 실패 0건, 신규 0건으로 안전 종료, 시크릿 미노출)
- [x] GitHub Secrets 등록 (GEMINI_API_KEY, SLACK_PROD_WEBHOOK_URL, GMAIL_USER, GMAIL_APP_PASSWORD) — `gh secret list`로 4개 등록 확인
- [x] STEP 18. GitHub Actions 주간 실행 (cron 추가) — 매주 월 09:00 KST(UTC `0 0 * * 1`), 기본 브랜치(main)에서 실행, 스케줄 실행은 항상 실제 발송 모드(dry_run은 수동 실행 전용). 첫 자동 실행: 2026-09-28(월) 09:00 KST 예정

---

## 작업 로그

새 작업을 시작하거나 끝낼 때마다 한 줄씩 추가한다.

| 날짜 | STEP | 한 일 | 결과 / 이슈 |
|---|---|---|---|
| 2026-09-23 | 사전준비 | Fork/Clone/브랜치/폴더 생성 | 완료 |
| 2026-09-23 | 사전준비 | 가상환경 생성 시도 | 루트 .venv에 잘못 설치됨 → chapter11 전용으로 재작업 |
| 2026-09-23 | 사전준비 | chapter11/ax-job-agent/.venv 재생성 및 패키지 설치 | 완료, where.exe python으로 경로 확인 |
| 2026-09-23 | STEP 01 | Claude Code로 notebook 생성 + 전용 커널 등록 | 완료 |
| 2026-09-23 | STEP 03 | robots.txt 확인 + 검색 페이지 1회 요청 테스트 | 성공 (200, 885건). AI크롤러 차단/브라우저UA 허용 판단 기록 |
| 2026-09-23 | STEP 04 | requests 정적 HTML에서 공고 카드 8건 파싱 | company_name/job_title/career/location/job_url 결측 0. posted_date는 정적 HTML에 없어 None |
| 2026-09-23 | STEP 04 | 카드 HTML 구조 재확인 (STEP 04-1/04-2) | 8개 카드 전부 우측 하단 날짜 div가 비어 있음 → JavaScript 렌더링 데이터로 판단 |
| 2026-09-23 | STEP 04b | Playwright 도입 (sync API, headless, 요청 1회) | Windows Jupyter 커널에서 sync API 오류(NotImplementedError) → 별도 스레드 + Proactor 루프로 우회 |
| 2026-09-23 | STEP 04b | career 버그 발견: 렌더링 HTML에 STEP 04 파싱 함수를 그대로 쓰면 날짜 span이 같은 클래스라 배지 없는 카드 4개의 career가 "07/15(수) 등록"으로 잡힘 | 렌더링 HTML에서는 날짜 두 항목만 뽑도록 방침 수정 → 해결. STEP 04 정본은 그대로 유지 (PROJECT_SPEC.md 10절 방침 수정) |
| 2026-09-23 | STEP 04b | posted_date/closing_date를 job_url 기준으로 jobs에 병합 | 8건 전부 채워짐, 매칭 실패 0건. "상시채용"은 텍스트 그대로 저장 |
| 2026-09-23 | STEP 05 | 날짜 병합된 jobs로 DataFrame 최종 확인 | df.shape (8,7), 7개 컬럼 전부 str, 결측 0, job_url 중복 0 |
| 2026-09-23 | STEP 06 | 문자열 strip + 연도 처리 규칙 적용(posted_date_parsed/closing_date_parsed) + job_url 중복 제거 → df_clean | 8→8행, closing_date_parsed 결측 1건(상시채용), 마감<등록 위반 0건, 요일 일치 검증 통과. 02/29는 알려진 한계로 기록 |
| 2026-09-23 | STEP 07 | job_url에서 job_id(GI_Read/ 뒤 숫자) 추출 → jobs_history.csv와 비교해 is_new 표시 → 신규만 append 저장 | job_id 추출 실패 0건, history 파일 신규 생성(8행×11열), 8건 전부 신규, job_id 중복/결측 0건 |
| 2026-09-23 | STEP 08 | 신규 공고(is_new=True)만 대상으로 pandas 통계 산출 (Gemini 미사용) | 신규 8건. career: 경력 3/경력3년↑ 2/기타 각 1, location: 경기 성남시 3/서울 각 구 1, 마감 임박 1위 ㈜아시아경제(09-28, 5일), 마감일 없음 1건(상시채용) |
| 2026-09-23 | STEP 09 | .gitignore/.env.example 생성, chapter11/.env 커밋 차단(chapter11/.gitignore), google-genai 설치, 공고 1건 Gemini 요약 테스트 | 키 로드 True, gemini-3.5-flash-lite 응답 정상. 회사명/경력 정확·추측 없음, 단 모집 직무(AX 담당 등) 누락 → STEP 10 검증 기준에 반영 |
| 2026-09-23 | STEP 10 | summarize_job() 함수로 신규 8건 전체 요약(호출 간 1초) → df_summary, 사람이 원문과 한 건씩 대조 | 8/8 성공. 사실 오류 0, 지어낸 내용 0, 직무 누락 1(아시아경제 부서명만). STEP 09에서 빠졌던 GS리테일 직무명이 이번엔 포함 → 응답 변동성(재현성) 이슈로 기록, 주기적 샘플 검증 권장 |
| 2026-09-23 | STEP 11 | 검증된 df_summary로 Markdown 보고서 생성 → reports/YYYY-MM-DD.md 저장 (Gemini 재호출 없음) | reports/2026-09-23.md 생성, 71줄/3505 bytes, 공고 8건·회사명/제목/요약 각 8/8 반영, 마감 임박 순(1위 아시아경제 D-5, 상시채용 맨 뒤) |
| 2026-09-23 | STEP 11 | 보고서 상단에 '요약 모델: {GEMINI_MODEL}' 줄 추가 → reports/2026-09-23.md 재생성(덮어쓰기) | 이전 파일과 비교해 요약 모델 줄 1줄만 추가(72줄/3545 bytes), Gemini 재호출 없음. STEP 12(Slack)는 워크스페이스/웹훅 미설정으로 보류 → STEP 13(Gmail)으로 진행 |
| 2026-09-23 | STEP 13 | .env.example에 GMAIL_USER/GMAIL_APP_PASSWORD 추가, send_gmail() 작성, 보고서를 본인에게 1건 테스트 발송 | 로드 True/True, 발송 성공, 실제 메일함 수신 확인(본문 72줄·8건 반영, 2026-09-23.md 첨부, 한글 깨짐 없음, Gmail 검사 통과) |
| 2026-09-23 | STEP 12 | (보류 해제) .env.example에 SLACK_PROD_WEBHOOK_URL 추가, src/notifier.py에 send_slack() 추가(3,500자 제한, 에러 메시지에 Webhook URL 미노출), 보고서 1건 발송 | 로드 True, HTTP 200, #팀스파르타-ax-2기-전체 채널(공용 실습 채널, 12명)에서 수신 확인: 8건 전체 반영, 마크다운 기호는 텍스트 그대로 표시 |
| 2026-09-23 | STEP 14 | 노트북 로직을 src/ 6개 모듈(crawler/preprocess/analyzer/gemini_client/reporter/notifier)로 이동, jobs_history.csv 실제 8건으로 리팩토링 전후 비교, career 셀렉터를 span.flex-shrink-0.text-typo-c1-13로 수정 | 30/30 일치(보고서는 글자 단위 동일), career 렌더링 HTML 8/8·정적 대체본 8/8 일치. 원본 정적 HTML은 STEP 09 response 변수 충돌로 유실(원인 수정). STEP 14-1 재호출 테스트는 중복이라 생략 |
| 2026-09-23 | STEP 15 | src/ 6개 모듈을 잇는 main.py 작성 (--keyword/--limit/--dry-run, 신규 0건이면 조기 종료, 발송이 모두 성공해야 history 갱신) | 가짜 함수로 분기 4가지 사전 테스트 통과. 사람이 dry-run·실제 모드 실행: 둘 다 신규 0건으로 외부 호출 없이 종료, 실행 모드 로그 정상. jobs_history.csv·보고서 파일 변경 없음 확인 |
| 2026-09-23 | STEP 16 | python main.py 로컬 실제 실행 | 성공, 신규 0건으로 외부 호출 없이 종료. '신규 있음' 전체 흐름은 강제 재현하지 않음 — 개별 로직 실제 호출 검증(STEP 04/09/10/12/13) + STEP 14 30/30 + main.py 모의 테스트(A~D)로 커버 판단, 실제 신규 공고가 뜨는 주에 end-to-end 확인 예정 |
| 2026-09-23 | 배포 | 커밋 전 정리(STEP 13 이메일 주소 마스킹, requirements.txt 버전 고정 작성) → 17개 파일만 명시적 add·커밋 → 작성자 이메일을 GitHub noreply 주소로 바꿔 amend → `git push -u origin ax-job-agent` | 커밋 6c59eb5 (+3,947줄), 민감정보 grep 8개 항목 모두 없음, 저장소 루트 requirements.txt는 제외. 내 Fork에 ax-job-agent 브랜치 생성 |
| 2026-09-23 | STEP 17 | job_url→job_id 병합 키 전환 (커밋 06587e3) — GitHub Actions에서만 발생한 listno 불안정 문제(첫 dry_run에서 매칭 실패 2건) 수정. 렌더링 페이지의 모든 카드에서 날짜 추출, checkout@v5·setup-python@v6 업그레이드 | 오프라인 3개 시나리오(차이 없음 / listno 변경 / listno+순서 변경) 모두 매칭 실패 0건·날짜 8/8 검증 + dry_run 재실행으로 매칭 실패 0건 확인. STEP 14 회귀 30/30 |
| 2026-09-23 | STEP 17 | Playwright 타임아웃 수정 (커밋 c261c06) — 첫 실제 실행이 page.goto의 load 대기 30초 초과로 실패(발송·history 변경 없음) → domcontentloaded + 60초 타임아웃 + 1회 재시도 | 오프라인 4개 케이스(1회차 성공 / goto 타임아웃 후 재시도 성공 / 셀렉터 타임아웃 후 재시도 성공 / 2회 모두 실패 시 에러) 검증, STEP 14 회귀 30/30. dry_run(run 35836348734)·실제 실행(run 35836468808) 모두 성공: 매칭 실패 0건, 신규 0건이라 발송·history 커밋 없음, 시크릿 미노출 |
| 2026-09-23 | STEP 18 | 워크플로우에 schedule(cron `0 0 * * 1`) 추가, dry_run 조건을 workflow_dispatch일 때만 적용하도록 변경 (커밋 d84e84d, ax-job-agent·main 반영) | YAML 파싱 OK, 이벤트별 분기 시뮬레이션(스케줄 → 항상 `python main.py`) 확인. workflow_dispatch dry_run(run 35836941850) 성공: 매칭 실패 0건, 신규 0건, 시크릿 미노출. main의 워크플로우 active + cron 등록 확인. 첫 자동 실행 2026-09-28(월) 09:00 KST 예정 |

---

## 다음 세션 시작할 때 이렇게 확인하세요

1. 이 파일의 "현재 상태" 섹션을 본다.
2. 위 STEP 체크리스트에서 마지막 `[x]`가 어디까지인지 본다.
3. `notebooks/ax_job_pipeline.ipynb`를 열어 마지막 셀의 "실행 결과 해석"을 읽는다.
4. `PROJECT_SPEC.md`의 원칙(6절)을 다시 한번 훑는다.
5. 다음 STEP 하나만 진행한다 (여러 STEP을 한 번에 하지 않는다).
