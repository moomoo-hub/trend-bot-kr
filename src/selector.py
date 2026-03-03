"""
키워드 선별 모듈

- 수집된 키워드 중 상위 3개 선별
- 이미 사용된 키워드는 제외 (used_keywords.json)
- 1일(24시간) 이내 사용된 키워드는 재사용 불가
- 만료된 키워드는 저장 시 자동 정리 (파일 크기 최대 ~21개 유지)
"""

import os
import json
from datetime import datetime, timedelta

USED_KEYWORDS_FILE = os.path.join(os.path.dirname(__file__), "used_keywords.json")
KEYWORD_TTL_DAYS = 1  # 키워드 유효 기간 (일)


def _safe_parse_dt(dt_str: str) -> datetime:
    """ISO 형식 datetime 안전 파싱. 실패 시 과거 시각 반환"""
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return datetime(1970, 1, 1)


def _load_used_keywords() -> list[dict]:
    """used_keywords.json에서 사용된 키워드 로드"""
    if not os.path.exists(USED_KEYWORDS_FILE):
        return []
    try:
        with open(USED_KEYWORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [경고] used_keywords.json 로드 실패: {e}", flush=True)
        return []


def _save_used_keywords(keywords: list[dict]) -> None:
    """사용된 키워드를 used_keywords.json에 저장"""
    try:
        with open(USED_KEYWORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(keywords, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  [경고] used_keywords.json 저장 실패: {e}", flush=True)


def _get_active_used_keywords() -> set[str]:
    """1일 미만인 사용된 키워드 반환 (당일 중복 발송 방지)"""
    used = _load_used_keywords()
    threshold = datetime.now() - timedelta(days=KEYWORD_TTL_DAYS)

    active = set()
    for item in used:
        if _safe_parse_dt(item.get("used_at", "")) > threshold:
            active.add(item["keyword"])

    return active


def _filter_new_keywords(keywords: list[dict]) -> list[dict]:
    """사용된 키워드 제외"""
    active_used = _get_active_used_keywords()
    filtered = [kw for kw in keywords if kw["keyword"] not in active_used]

    if not filtered:
        # 모든 키워드가 이미 사용된 경우: 전체 목록 반환
        print("  [선별] 모든 키워드가 최근 사용됨. 전체 목록에서 선택합니다.", flush=True)
        return keywords

    return filtered


def select_keywords(all_keywords: list[dict]) -> list[dict]:
    """수집된 키워드에서 사용되지 않은 상위 3개 선별"""
    print("\n[선별] 키워드 선별 중...", flush=True)

    # 사용된 키워드 제외
    candidates = _filter_new_keywords(all_keywords)

    if not candidates:
        print("  [선별] 후보 키워드 없음", flush=True)
        return []

    # 상위 3개 선택
    selected = candidates[:3]
    selected_names = [kw['keyword'] for kw in selected]
    selected_topics = [kw.get('topic', '기타') for kw in selected]
    print(f"  [선별] 선정된 키워드: {', '.join([f'{kw}[{topic}]' for kw, topic in zip(selected_names, selected_topics)])}", flush=True)
    return selected


def mark_keywords_used(selected_keywords: list[dict]) -> None:
    """선정된 키워드를 사용됨으로 표시 (dict 또는 str 모두 지원)"""
    now_dt = datetime.now()
    threshold = now_dt - timedelta(days=KEYWORD_TTL_DAYS)

    # 만료된 항목 먼저 정리 (1일 이상 지난 것 제거 → 파일 크기 제한)
    used = _load_used_keywords()
    used = [
        item for item in used
        if _safe_parse_dt(item.get("used_at", "")) > threshold
    ]

    # 새 항목 추가
    now = now_dt.isoformat()
    for item in selected_keywords:
        keyword = item['keyword'] if isinstance(item, dict) else item
        used.append({
            "keyword": keyword,
            "used_at": now,
        })

    _save_used_keywords(used)
    print(f"  [기록] {len(selected_keywords)}개 키워드 사용 기록 (총 {len(used)}개 보관)", flush=True)
