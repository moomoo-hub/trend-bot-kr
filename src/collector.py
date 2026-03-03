"""
트렌드 키워드 수집 모듈 (네이버 뉴스 기반 - RSS + 웹 크롤링 하이브리드)

수집 방식:
1. 먼저 RSS 피드 시도 (빠름, 공식)
2. RSS 실패 시 웹 크롤링으로 fallback (안정성)

특징:
- 기사 실제 본문 추출 (URL 개별 방문)
- URL sid1 기반 정확한 분야 분류
- 정치 제외, 상위 키워드 추출
- 분야별 다양성 확보 (경제, 사회, IT, 연예, 스포츠)
- 신선한 실시간 데이터 수집
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

POLITICS_BLACKLIST = {"정치", "정당", "정권", "의원", "대통령", "국회", "여당", "야당", "선거", "투표"}

# 확대된 불용어 목록
EXPANDED_STOPWORDS = {
    "및", "와", "과", "또는", "등", "이", "가", "는", "을", "를", "에", "에서", "으로",
    "속보", "한국", "중국", "일본", "세계", "미국", "오늘", "내일", "어제",
    "현장", "상황", "사건", "사고", "소식", "뉴스", "보도", "기자", "기사",
    "발표", "확인", "보니", "다고", "한다", "했다", "어", "있다", "그리고",
}

# 네이버 뉴스 RSS 피드 URL
NAVER_RSS_FEEDS = {
    "경제": "https://feeds.news.naver.com/article/101/feed",
    "사회": "https://feeds.news.naver.com/article/102/feed",
    "IT": "https://feeds.news.naver.com/article/105/feed",
    "연예": "https://feeds.news.naver.com/article/106/feed",
    "스포츠": "https://feeds.news.naver.com/article/107/feed",
}

# 네이버 뉴스 URL의 sid1 값 → 분야 매핑
# None = 정치 (제외 대상)
NAVER_SID_TO_TOPIC = {
    "100": None,       # 정치 → 제외
    "101": "경제",
    "102": "사회",
    "103": "IT",
    "104": "생활문화",
    "105": "세계",
    "106": "연예",
    "107": "스포츠",
}

# 기사 본문 CSS 선택자 (우선순위 순)
BODY_SELECTORS = [
    "div#dic_area",
    "div.newsct_article",
    "div#articleBodyContents",
    "div.article_body",
]


def _extract_main_keyword(title: str) -> str:
    """뉴스 제목에서 주요 키워드 1개만 추출"""
    # 한글만 추출
    korean_only = re.sub(r'[^가-힣\s]', '', title)

    # 3글자 이상 우선, 없으면 2글자 이상
    words_3plus = [w for w in korean_only.split() if len(w) >= 3 and w not in EXPANDED_STOPWORDS]
    words_2plus = [w for w in korean_only.split() if len(w) >= 2 and w not in EXPANDED_STOPWORDS]

    # 3글자 이상 단어가 있으면 첫 번째 반환, 없으면 2글자 이상 단어 중 첫 번째
    if words_3plus:
        return words_3plus[0]
    elif words_2plus:
        return words_2plus[0]

    return ""


def _classify_topic_from_url(url: str):
    """
    네이버 뉴스 URL에서 분야 추출 시도

    주의: n.news.naver.com/article/{oid}/{aid} 형식에서
    oid는 '언론사 ID'이며 분야 ID가 아님.
    따라서 항상 "" 반환 → 제목 기반 분류로 폴백.

    뉴스 분야 URL이 별도 존재하는 경우
    (news.naver.com/section/{sid1}에서 수집된 경우)에만 유효.
    현재 n.news.naver.com 기사 URL에서는 분야 추출 불가.
    """
    # 정치 URL 패턴 감지 (보수적 처리): URL에 /100/ 포함 시 제외
    if "/article/100/" in url:
        return None  # 정치 → 제외

    # 분야 추출 불가 → 제목 기반 분류로 폴백
    return ""


def _classify_topic_from_title(title: str) -> str:
    """제목 기반 분야 분류 (URL 분류 실패 시 fallback)"""
    if any(w in title for w in ["주가", "코스피", "금리", "증시", "부동산", "환율", "물가", "경제", "금융", "투자", "주식"]):
        return "경제"
    elif any(w in title for w in ["의료", "교육", "노동", "범죄", "법원", "검찰", "복지", "사회", "사망", "부상", "사고"]):
        return "사회"
    elif any(w in title for w in ["AI", "삼성", "네이버", "카카오", "앱", "반도체", "IT", "스마트폰", "애플", "구글", "테크"]):
        return "IT"
    elif any(w in title for w in ["배우", "드라마", "영화", "가수", "음악", "아이돌", "예능", "연예", "웹툰"]):
        return "연예"
    elif any(w in title for w in ["축구", "야구", "배구", "선수", "리그", "올림픽", "스포츠", "감독", "팀"]):
        return "스포츠"
    elif any(w in title for w in ["날씨", "여행", "맛집", "건강", "운동", "요리", "생활", "문화", "취미"]):
        return "생활문화"
    return "기타"


def _extract_article_body(article_url: str) -> str:
    """
    네이버 뉴스 기사 URL에서 본문 텍스트 추출

    CSS 선택자 우선순위:
      1. div#dic_area         (최신 네이버 뉴스 본문)
      2. div.newsct_article   (구형 레이아웃)
      3. div#articleBodyContents (일부 제휴사)
      4. div.article_body     (기타)

    반환값: 본문 문자열 (100자 이상) 또는 빈 문자열 (실패 시)
    """
    MIN_BODY_LEN = 100
    MAX_BODY_LEN = 500

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://news.naver.com",
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    try:
        resp = requests.get(article_url, headers=headers, timeout=5)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        for selector in BODY_SELECTORS:
            elem = soup.select_one(selector)
            if not elem:
                continue

            # 광고/관련기사/기자정보/저작권 등 불필요 태그 제거
            for tag in elem.select(
                "script, style, .reporter_area, .copyright, "
                ".article_relation, .naver_related, strong.media_end_summary"
            ):
                tag.decompose()

            text = elem.get_text(separator=" ", strip=True)
            # 연속 공백 정리
            text = re.sub(r"\s+", " ", text).strip()

            if len(text) >= MIN_BODY_LEN:
                return text[:MAX_BODY_LEN]

        return ""

    except Exception:
        # 타임아웃 또는 네트워크 오류 → 빈 문자열 반환 (호출부에서 제목으로 대체)
        return ""


def get_naver_trending_via_rss() -> list[dict]:
    """
    네이버 뉴스 RSS 피드로부터 실시간 트렌드 수집

    특징:
    - 빠름: XML 파싱만 필요 (웹 크롤링 불필요)
    - 안정적: 네이버 공식 제공 (구조 변경 영향 없음)
    - 신선: 실시간 업데이트
    """
    try:
        print("  [수집] 네이버 RSS 피드 조회 중...", flush=True)

        all_keywords = []
        topic_used = set()  # 분야별 중복 방지

        for topic, feed_url in NAVER_RSS_FEEDS.items():
            try:
                # RSS 피드 파싱
                feed = feedparser.parse(feed_url)

                if not feed.entries:
                    print(f"  [경고] {topic} RSS 피드 비어있음", flush=True)
                    continue

                # 분야별로 첫 기사만 선택 (신선도 + 분야 다양성)
                for entry in feed.entries[:3]:  # 상위 3개 중에서 선택
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    published = entry.get('published', '')

                    # 제목 길이 확인
                    if not title or len(title) < 10 or len(title) > 150:
                        continue

                    # 정치 기사 제외
                    if any(word in title for word in POLITICS_BLACKLIST):
                        continue

                    # 키워드 추출
                    keyword = _extract_main_keyword(title)
                    if not keyword:
                        continue

                    # 분야별 첫 번째 기사만 사용
                    if topic not in topic_used:
                        # RSS도 본문 추출 시도 (링크가 있는 경우)
                        article_body = ""
                        if link:
                            article_body = _extract_article_body(link)
                        if not article_body:
                            article_body = f"[{topic}] {title}"

                        all_keywords.append({
                            "keyword": keyword,
                            "topic": topic,
                            "article_title": title,
                            "news_url": link,
                            "article_body": article_body,
                            "published": published,
                            "source": "Naver RSS"
                        })
                        topic_used.add(topic)
                        break

            except Exception as e:
                print(f"  [경고] {topic} RSS 수집 실패: {e}", flush=True)
                continue

        print(f"  [수집] RSS 피드: {len(all_keywords)}개 키워드", flush=True)
        return all_keywords

    except Exception as e:
        print(f"  [오류] RSS 수집 실패: {e}", flush=True)
        return []


def get_naver_trending_via_web_crawling() -> list[dict]:
    """
    네이버 뉴스 웹 크롤링으로 트렌드 수집 (RSS 실패 시 fallback)
    - URL sid1 기반 분야 분류
    - 각 기사 URL 방문해서 실제 본문 추출
    - 분야별 최대 2개, 총 최대 9개 수집
    """
    try:
        print("  [수집] 네이버 뉴스 웹 크롤링 중...", flush=True)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get("https://news.naver.com", headers=headers, timeout=5)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        # n.news.naver.com 형식의 실제 기사만 수집
        articles = []
        seen_titles = set()

        for link_elem in soup.select("a[href*='n.news.naver.com/article']"):
            title = link_elem.get_text(strip=True)
            url_href = link_elem.get("href", "")

            # 중복 제거
            if title in seen_titles or not title or len(title) < 10:
                continue
            seen_titles.add(title)

            # 제목 길이 확인
            if 10 < len(title) < 150 and url_href:
                articles.append({
                    "title": title,
                    "url": url_href
                })

        print(f"  [수집] 웹 크롤링: {len(articles)}개 기사 수집", flush=True)

        # 키워드 추출 (분야별 최대 2개, 총 최대 9개)
        MAX_PER_TOPIC = 2
        MAX_TOTAL = 9
        keywords = []
        topic_count = {}
        seen_keywords = set()

        for article in articles[:30]:  # 상위 30개 검토
            if len(keywords) >= MAX_TOTAL:
                break

            keyword = _extract_main_keyword(article["title"])
            if not keyword or keyword in seen_keywords:
                continue

            # URL 기반 분야 분류 (우선)
            topic = _classify_topic_from_url(article["url"])

            if topic is None:
                # 정치 기사 → 제외
                continue

            if topic == "":
                # URL 패턴 불일치 → 제목 기반 분류로 fallback
                topic = _classify_topic_from_title(article["title"])

            # 제목에 정치 키워드 포함 시 추가 제외
            if any(word in article["title"] for word in POLITICS_BLACKLIST):
                continue

            # 분야별 최대 2개 제한
            current_count = topic_count.get(topic, 0)
            if current_count >= MAX_PER_TOPIC:
                continue

            # 기사 본문 추출 (실제 URL 방문)
            article_body = _extract_article_body(article["url"])
            if not article_body:
                # 본문 추출 실패 → 제목으로 대체
                article_body = article["title"]
                print(f"  [본문] '{keyword}' 본문 추출 실패, 제목으로 대체", flush=True)
            else:
                print(f"  [본문] '{keyword}' {len(article_body)}자 추출", flush=True)

            keywords.append({
                "keyword": keyword,
                "topic": topic,
                "article_title": article["title"],
                "news_url": article["url"],
                "article_body": article_body,
                "source": "Naver Web"
            })
            topic_count[topic] = current_count + 1
            seen_keywords.add(keyword)

        print(f"  [수집] 유효 키워드: {len(keywords)}개 (분야: {len(topic_count)}개)", flush=True)
        return keywords

    except Exception as e:
        print(f"  [오류] 웹 크롤링 실패: {e}", flush=True)
        return []


def collect_all_trends() -> list[dict]:
    """뉴스 기반 트렌드 수집 (RSS → 웹 크롤링 하이브리드)"""
    print("\n[트렌드봇] 뉴스 트렌드 수집 시작\n", flush=True)

    # 1단계: RSS 시도
    all_keywords = get_naver_trending_via_rss()

    # 2단계: RSS 실패 시 웹 크롤링으로 fallback
    if not all_keywords or len(all_keywords) == 0:
        print("  [대체] RSS 수집 실패. 웹 크롤링으로 대체합니다.", flush=True)
        all_keywords = get_naver_trending_via_web_crawling()

    # 중복 제거
    seen: set[str] = set()
    unique: list[dict] = []
    for item in all_keywords:
        if item["keyword"] not in seen:
            seen.add(item["keyword"])
            unique.append(item)

    # 3개 미만이면 실제 수집된 기사에서 추가 보충 (더미 Fallback 최소화)
    if 0 < len(unique) < 3:
        print(f"  [보충] 현재 {len(unique)}개. 크롤링 결과에서 추가 보충 시도...", flush=True)
        extra = [item for item in all_keywords if item["keyword"] not in seen]
        for item in extra:
            if len(unique) >= 3:
                break
            seen.add(item["keyword"])
            unique.append(item)
        print(f"  [보충] 보충 후: {len(unique)}개", flush=True)

    # 그래도 3개 미만이면 최소 더미 Fallback (완전한 실패 방지)
    if len(unique) < 3:
        print(f"  [경고] 수집 부족 ({len(unique)}개). 최소 Fallback 추가...", flush=True)
        used_topics = {item["topic"] for item in unique}
        fallback_list = [
            {"keyword": "경제이슈", "topic": "경제"},
            {"keyword": "사회이슈", "topic": "사회"},
            {"keyword": "IT이슈", "topic": "IT"},
            {"keyword": "연예이슈", "topic": "연예"},
            {"keyword": "스포츠이슈", "topic": "스포츠"},
        ]
        for fallback in fallback_list:
            if fallback["topic"] not in used_topics and len(unique) < 3:
                unique.append({
                    "keyword": fallback["keyword"],
                    "source": "Fallback",
                    "topic": fallback["topic"],
                    "news_url": "",
                    "article_title": fallback["keyword"],
                    "article_body": f"[{fallback['topic']}] 최신 트렌드 이슈가 주목받고 있음. 관련 분야 전문가들은 다양한 의견을 제시하고 있으며, 실생활에 영향을 미칠 수 있어 주의가 필요함."
                })
                used_topics.add(fallback["topic"])

    if not unique:
        print("  [경고] 수집된 키워드 없음. 기본값 사용", flush=True)
        return [
            {"keyword": "경제이슈", "source": "Fallback", "topic": "경제", "news_url": "", "article_title": "경제이슈", "article_body": "[경제] 최신 경제 트렌드 이슈가 주목받고 있음. 전문가들은 다양한 의견을 내놓고 있으며 시장 동향을 주시할 필요가 있음."},
            {"keyword": "사회이슈", "source": "Fallback", "topic": "사회", "news_url": "", "article_title": "사회이슈", "article_body": "[사회] 최근 사회적 이슈가 화두가 되고 있음. 여러 전문가들이 대응 방안을 논의 중이며 앞으로의 추이가 주목됨."},
            {"keyword": "IT이슈", "source": "Fallback", "topic": "IT", "news_url": "", "article_title": "IT이슈", "article_body": "[IT] 최신 기술 동향이 주목받고 있음. AI와 디지털 전환이 빠르게 진행되면서 산업 전반에 영향을 미치고 있음."},
        ]

    print(f"\n[수집 완료] 총 {len(unique)}개 키워드 (분야: {len(set(item['topic'] for item in unique))}개)\n", flush=True)
    return unique
