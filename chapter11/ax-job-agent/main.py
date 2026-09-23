"""AX 채용정보 주간 파이프라인 (STEP 15).

수집 → 전처리 → 신규 판별 → 통계 → (신규가 있으면) Gemini 요약 → 보고서 저장 → Gmail/Slack 발송 → history 갱신

사용법:
    python main.py --dry-run           # 먼저 이걸로 확인 (Gemini·발송·history 저장 없음)
    python main.py                     # 실제 실행
    python main.py --keyword AX --limit 8
"""

import argparse
import sys

import pandas as pd

from src import analyzer, crawler, gemini_client, notifier, preprocess, reporter


def parse_args():
    parser = argparse.ArgumentParser(description="AX 채용정보 주간 리포트 파이프라인")
    parser.add_argument("--keyword", default="AX", help="검색어 (기본값: AX)")
    parser.add_argument("--limit", type=int, default=crawler.DEFAULT_LIMIT, help="수집할 공고 수 (기본값: 8)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Gemini 호출, 보고서 저장, 이메일/Slack 발송, history 저장을 하지 않고 무엇을 했을지만 출력",
    )
    return parser.parse_args()


def print_stats(stats):
    print(f"  신규 공고 건수: {stats['new_count']}")
    print(f"  career 분포: {stats['career_counts']}")
    print(f"  location 분포: {stats['location_counts']}")
    print(f"  마감일 없는 공고: {stats['no_deadline_count']}건 {stats['no_deadline_texts']}")
    print("  마감 임박 상위:")
    for _, row in stats["closing_soon"].iterrows():
        print(f"    - {row['company_name']} | {row['closing_date_parsed']:%Y-%m-%d} (D-{row['days_left']}) | {row['job_title']}")


def main():
    args = parse_args()
    today = pd.Timestamp.now().normalize()
    history_path = analyzer.DEFAULT_HISTORY_PATH

    print("[실행 모드: DRY RUN]" if args.dry_run else "[실행 모드: 실제 발송]")
    print(f"기준일: {today:%Y-%m-%d} | 검색어: {args.keyword} | 수집 수: {args.limit}")

    # 1) 수집 (dry-run이어도 실제 요청: robots.txt 1회 + 정적 페이지 1회 + Playwright 1회)
    print("\n[1/6] 수집")
    jobs = crawler.fetch_job_list(args.keyword, limit=args.limit)
    print(f"  수집 {len(jobs)}건")

    # 2) 전처리
    print("\n[2/6] 전처리")
    df_clean = preprocess.clean_jobs(jobs, today=today)
    print(f"  {len(jobs)}건 → {len(df_clean)}건 (job_url 중복 제거 후)")

    # 3) 신규 판별 (history 저장은 발송이 끝난 뒤에)
    print("\n[3/6] 신규 판별")
    df_checked = analyzer.detect_new_jobs(df_clean, history_path)
    df_new = df_checked[df_checked["is_new"]].reset_index(drop=True)
    print(f"  신규 {len(df_new)}건 / 전체 {len(df_checked)}건 (job_id 추출 실패 {int(df_checked['job_id'].isna().sum())}건)")

    # 4) 통계
    print("\n[4/6] 통계")
    stats = analyzer.summarize_stats(df_new, today=today)
    print_stats(stats)

    if df_new.empty:
        print("\n신규 공고가 없다. Gemini 호출, 보고서 저장, 발송, history 저장 없이 종료한다.")
        return 0

    report_path = reporter.default_report_path(today)
    subject = f"AX 채용정보 주간 리포트 ({today:%Y-%m-%d})"

    if args.dry_run:
        print("\n[5/6] 요약 + 보고서 (DRY RUN - 실행하지 않음)")
        print(f"  할 일: Gemini({gemini_client.GEMINI_MODEL})로 {len(df_new)}건 요약 (호출 간 {gemini_client.SLEEP_SECONDS}초)")
        print(f"  할 일: 보고서 저장 → {report_path.relative_to(reporter.PROJECT_ROOT).as_posix()} (같은 날 파일이 있으면 덮어씀)")
        print("\n[6/6] 발송 + history (DRY RUN - 실행하지 않음)")
        print(f"  할 일: Gmail 발송 (GMAIL_USER 본인, 제목 '{subject}', 보고서 첨부)")
        print("  할 일: Slack 발송 (SLACK_PROD_WEBHOOK_URL 채널)")
        print(f"  할 일: history 갱신 → 신규 {len(df_new)}건 추가 ({history_path.relative_to(analyzer.PROJECT_ROOT).as_posix()})")
        print("\nDRY RUN 종료. 실제로 실행하려면 --dry-run 없이 실행한다.")
        return 0

    # 5) 요약 + 보고서
    print("\n[5/6] 요약 + 보고서")
    summaries = gemini_client.summarize_jobs(df_new)
    df_summary = df_new.copy()
    df_summary["gemini_summary"] = [s if s is not None else "(요약 실패)" for s in summaries]
    failed_count = sum(s is None for s in summaries)
    print(f"  요약 {len(summaries) - failed_count}건 (실패 {failed_count}건)")

    report_md = reporter.build_report_markdown(df_summary, report_date=today)
    report_path = reporter.save_report(report_md, report_path)
    print(f"  보고서 저장: {report_path.relative_to(reporter.PROJECT_ROOT).as_posix()} ({len(report_md.splitlines())}줄)")

    # 6) 발송 → 모두 성공하면 history 갱신
    print("\n[6/6] 발송 + history")
    send_ok = True
    try:
        notifier.send_gmail(subject=subject, body=report_md, attachment_path=report_path)
        print("  Gmail 발송: 성공")
    except Exception as e:  # 한 채널이 실패해도 다른 채널은 시도한다
        send_ok = False
        print(f"  Gmail 발송: 실패 ({type(e).__name__}: {e})")
    try:
        status = notifier.send_slack(report_md)
        print(f"  Slack 발송: 성공 (HTTP {status})")
    except Exception as e:
        send_ok = False
        print(f"  Slack 발송: 실패 ({type(e).__name__}: {e})")

    if not send_ok:
        # history를 갱신하지 않으면 다음 실행에서 같은 공고가 다시 신규로 잡혀 재발송된다
        print("  발송 실패가 있어 history를 갱신하지 않는다 (다음 실행 때 다시 시도).")
        return 1

    history_rows = analyzer.update_history(df_checked, history_path)
    print(f"  history 갱신: 신규 {len(df_new)}건 추가 → 총 {history_rows}행")
    print("\n완료.")
    return 0


if __name__ == "__main__":
    # Windows 콘솔(cp949)에서 "•", "㈜" 등 출력이 깨지거나 에러 나지 않도록
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
