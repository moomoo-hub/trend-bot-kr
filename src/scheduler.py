"""
스케줄러 및 자가 수복 에러 핸들러

- 2시간마다 실행
- 오류 발생 시 최대 3회 재시도
- 해결 불가능 시 텔레그램으로 보고
"""

import time
import schedule
import logging
from datetime import datetime
from pathlib import Path
from collector import collect_all_trends
from selector import select_keywords, mark_keywords_used
from writer import write_posts
from sender import send_posts, send_error_report

# 로깅 설정
log_file = Path.home() / "trendbot_scheduler.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [60, 120, 180]  # 초 단위 (1분, 2분, 3분)


def run_with_retry(func, step_name: str):
    """재시도 로직 포함 함수 실행"""
    for i, delay in enumerate([0] + RETRY_DELAYS):
        try:
            if delay > 0:
                logger.info(f"[재시도] {delay}초 후 {step_name} 재시도...")
                time.sleep(delay)
            return func()
        except Exception as e:
            if i == MAX_RETRIES:
                error_msg = str(e)[:100]
                logger.error(f"[실패] {step_name} {MAX_RETRIES}회 재시도 후 실패: {error_msg}")
                send_error_report(step_name, error_msg)
                return None
            logger.warning(f"[오류] {step_name} 시도 {i+1} 실패: {str(e)[:50]}...")


def run_cycle(skip_time_check: bool = False) -> None:
    """한 사이클: 수집 → 선별 → 작성 → 발송"""
    # 운영 시간 확인 (09:00 ~ 21:59)
    if not skip_time_check:
        hour = datetime.now().hour
        if hour < 9 or hour >= 22:
            logger.info(f"현재 {hour:02d}시 - 운영 시간 외(09:00~21:59). 스킵.")
            return
    else:
        logger.info("⭐ [테스트 모드] 시간 체크를 무시하고 실행합니다.")

    logger.info("=" * 60)
    logger.info("트렌드봇 사이클 시작")
    logger.info("=" * 60)

    # 1. 수집
    keywords = run_with_retry(
        lambda: collect_all_trends(),
        "키워드 수집"
    )
    if not keywords:
        logger.error("키워드 수집 실패. 다음 주기에 재시도.")
        return

    # 2. 선별 (재시도 없음, fallback으로 처리)
    try:
        selected = select_keywords(keywords)
        if not selected or len(selected) < 3:
            # 부족하면 추가 채우기
            selected_keywords = {kw["keyword"] for kw in selected}
            extra = [kw for kw in keywords if kw["keyword"] not in selected_keywords]
            selected.extend(extra[:(3 - len(selected))])
    except Exception as e:
        logger.warning(f"키워드 선별 실패: {e}. Fallback 사용.")
        selected = keywords[:3]

    if not selected:
        logger.error("키워드 선별 실패. 다음 주기에 재시도.")
        return

    # 3. 작성
    posts = run_with_retry(
        lambda: write_posts(selected),
        "게시글 작성"
    )
    if not posts:
        logger.error("게시글 작성 실패. 다음 주기에 재시도.")
        return

    # 4. 발송
    success = run_with_retry(
        lambda: send_posts(posts),
        "텔레그램 발송"
    )

    # 5. 키워드 사용 기록 (발송 성공 여부와 무관)
    mark_keywords_used(selected)

    logger.info("=" * 60)
    if success:
        logger.info("[완료] 사이클 완료 (텔레그램 발송 완료)")
    else:
        logger.warning("[경고] 사이클 완료 (일부 오류 발생)")
    logger.info("=" * 60)


def start_scheduler() -> None:
    """2시간마다 실행 스케줄러 시작"""
    logger.info("[스케줄러] 시작 (2시간 간격)")
    logger.info(f"로그 파일: {log_file}")

    # 즉시 1회 실행
    run_cycle()

    # 2시간마다 스케줄
    schedule.every(2).hours.do(run_cycle)
    logger.info("다음 사이클은 2시간 후에 자동 실행됩니다.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # 30초마다 스케줄 체크
    except KeyboardInterrupt:
        logger.info("[스케줄러] 사용자 중단. 종료합니다.")
    except Exception as e:
        logger.error(f"[스케줄러] 예상치 못한 오류: {e}")
        send_error_report("스케줄러", str(e)[:100])
        raise
