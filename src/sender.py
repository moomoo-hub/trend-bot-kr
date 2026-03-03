"""
텔레그램 발송 모듈

- Telegram Bot API로 메시지 발송
- 에러 보고도 텔레그램으로
"""

import os
import requests
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

POLITICS_BLACKLIST = {"정치", "정당", "정권", "의원", "대통령", "국회", "여당", "야당", "선거", "투표"}
ONSEUMCHE_MARKERS = {"임", "함", "인 듯", "됨", "었음", "다고 함", "더라", "하더라"}


def _validate_posts(posts: list[dict]) -> tuple[bool, list[str]]:
    """규칙 준수 여부 검증"""
    errors = []

    # 1. 정치 키워드 제외 확인
    for post in posts:
        keyword = post.get('keyword', '')
        if keyword in POLITICS_BLACKLIST:
            errors.append(f"[정치] 키워드 '{keyword}'는 정치 키워드 (제외 필요)")

    # 2. 최소 1개 이상 포스트 확인
    if len(posts) < 1:
        errors.append(f"[분야] 포스트 부족: {len(posts)}개")

    # 3. 각 포스트 검증
    for i, post in enumerate(posts, 1):
        keyword = post.get('keyword', '')
        title = post.get('title', '')
        body = post.get('body', '')
        url = post.get('news_url', '')
        is_fallback = post.get('source', '') == 'Fallback'

        # 3-1. 링크 확인 (Fallback 제외)
        if not is_fallback and (not url or not url.startswith('http')):
            errors.append(f"[링크] {i}번 포스트 '{keyword}': 링크 없음")

        # 3-2. 길이 확인 (제목 30~45자, 본문 350~450자)
        title_len = len(title)
        body_len = len(body)
        if title_len < 30 or title_len > 45:
            errors.append(f"[길이] {i}번 포스트 '{keyword}' 제목: {title_len}자 (30~45자 필수)")
        if body_len < 350 or body_len > 450:
            errors.append(f"[길이] {i}번 포스트 '{keyword}' 본문: {body_len}자 (350~450자 필수)")

        # 3-3. 음슴체 톤 확인 (Fallback 제외)
        if not is_fallback:
            onseumche_count = sum(body.count(marker) for marker in ONSEUMCHE_MARKERS)
            if onseumche_count < 1:
                errors.append(f"[음슴체] {i}번 포스트 '{keyword}': 음슴체 마커 부족")

        # 3-4. 라벨 확인 (제목:, 본문: 금지)
        full_text = title + body
        if '제목:' in full_text or '본문:' in full_text:
            errors.append(f"[라벨] {i}번 포스트 '{keyword}': 라벨 포함 (제거 필요)")

    passed = len(errors) == 0
    return passed, errors


def _send_telegram_message(message: str) -> bool:
    """텔레그램으로 메시지 발송"""
    if not TOKEN or not CHAT_ID:
        print("  [경고] TELEGRAM_TOKEN/CHAT_ID 미설정. 발송 스킵.", flush=True)
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            return True
        else:
            print(f"  [오류] 텔레그램 발송 실패: {res.status_code}", flush=True)
            return False
    except Exception as e:
        print(f"  [오류] 텔레그램 발송 오류: {e}", flush=True)
        return False


def send_posts(posts: list[dict]) -> bool:
    """생성된 게시글을 텔레그램으로 발송 (검증 후)"""
    print("\n[검증] 규칙 준수 여부 확인 중...", flush=True)

    # 규칙 검증
    passed, errors = _validate_posts(posts)

    if not passed:
        print("  [검증 실패]", flush=True)
        for error in errors:
            print(f"    - {error}", flush=True)
        return False

    print("  [검증 완료] 모든 규칙 준수", flush=True)
    print("\n[발송] 텔레그램 메시지 생성 중...", flush=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"[트렌드봇] {now}\n\n"

    for i, post in enumerate(posts, 1):
        topic = post.get('topic', '기타')
        message += f"{i}. <b>{post['keyword']}</b> [{topic}]\n"
        message += f"{post['title']}\n"
        message += f"{post['body']}\n"

        # 뉴스 링크 추가
        if post.get('news_url'):
            message += f"{post['news_url']}\n"

        message += "\n"

    print(f"  → {len(posts)}개 게시글 메시지 준비 완료", flush=True)

    if _send_telegram_message(message):
        print("  [발송 완료] 텔레그램으로 전송됨", flush=True)
        return True
    else:
        print("  [발송 실패]", flush=True)
        return False


def send_error_report(step: str, error: str) -> bool:
    """에러를 텔레그램으로 보고"""
    if not TOKEN or not CHAT_ID:
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = (
        f"⚠️ <b>[트렌드봇 오류]</b> {now}\n\n"
        f"<b>단계:</b> {step}\n"
        f"<b>오류:</b> <code>{error[:100]}</code>"
    )

    return _send_telegram_message(message)
