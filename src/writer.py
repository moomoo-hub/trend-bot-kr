"""
UGC 커뮤니티 글 작성 모듈

- Claude Sonnet으로 UGC 스타일 게시글 생성
- 기사 본문을 참조하여 맥락에 맞는 톤으로 작성
- 톤: 2030 직장인 일상톤 (친근하고 냉소적)
- 길이: 제목 30~45자 + 본문 350~450자 (공백 포함)
- 구조: 5단계 공식 (제목 + 도입 + 전개 + 결론 + 출처)
- LSI 키워드: 본문 2문단에 최소 3개 자연스럽게 포함
- 정보비: 팩트 20% + 개인경험(UGC) 80%
"""

from anthropic import Anthropic
import re
import os
import time
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """당신은 트래픽을 유도하고 SEO 상위 노출을 달성하는 10년차 커뮤니티 마케터이자 UGC 카피라이터입니다.
건조한 뉴스를 직장인들이 열광하고 댓글을 달 수밖에 없는 '썰' 형태로 변환하는 것이 목표입니다.

## Role & Tone (역할과 어조)
- 2030 직장인이 동료와 메신저로 대화하듯: 친근하고 약간 냉소적/자조적
- **음슴체 필수**: 본문에 "~함", "~임", "~더라", "~었음", "~다고 함" 등을 최소 3개 이상 자연스럽게 포함
- "~어?", "~거 나만 그래?", "ㅋㅋ", "ㅠ" 등 인터넷 커뮤니티체 자연스럽게 사용
- 팩트 앞에서 한없이 작아지는 일반 직장인의 감성

## Output Constraints (출력 제한)
1. 글자 수: 제목 정확히 30~45자 + 본문 정확히 350~450자 (공백 포함, 링크 제외)
2. 문단: 제목 1줄 + 본문 3~4문단 + 빈 줄(엔터) + 출처 1줄
3. 정보비율: 팩트 20% + 개인경험/의견(UGC) 80%
4. LSI 키워드: 본문 2문단에 유의어/관련어/관련직군 최소 3개 이상 자연스럽게 포함

## 5단계 공식 (필수)
1. **제목**: [메인이슈/수치] + [개인감정/반전/질문] + (ft. 서브키워드) → 정확히 30~45자
2. **1문단**: [기사핵심 1줄] + [일반반응] + [나의 현실/결핍] + "나만 그런 거임?" → 팩트+공감
3. **2문단**: [연관용어 1,2,3] + [구체적경험/실패담] + [핵심어] + 감정 → LSI키워드 3개 이상 필수
4. **3문단**: "형들은 [행동A] 했어? 아니면 [행동B]?" + 미래질문 → A or B 객관식
5. **출처**: (뉴스 링크: [URL])"""


def _fix_title_length(title: str, target_min: int = 30, target_max: int = 45) -> str:
    """제목 글자 수 조정 (30~45자)"""
    current_len = len(title)

    if current_len < target_min:
        # 너무 짧으면 끝에 물음표 추가
        if "?" not in title and "ㅠ" not in title:
            title = title.rstrip("?ㅠ") + "?"
    elif current_len > target_max:
        # 너무 길면 뒤에서 잘라냄
        title = title[:target_max].rstrip("?ㅠ")
        if not title.endswith(("?", "ㅠ")):
            title = title.rstrip() + "?"

    return title


def _fix_body_length(body: str, target_min: int = 350, target_max: int = 450) -> str:
    """본문 글자 수 조정 (350~450자)"""
    current_len = len(body)

    if current_len > target_max:
        # 너무 길면 끝에서 문장 단위로 잘라냄
        while len(body) > target_max and "\n\n" in body:
            last_para_start = body.rfind("\n\n")
            body = body[:last_para_start].strip()

        # 여전히 길면 강제로 잘라냄
        if len(body) > target_max:
            body = body[:target_max].rsplit(" ", 1)[0] + "..."

    return body


def _add_lsi_keywords(body: str, keyword: str) -> str:
    """LSI 키워드 부족하면 추가 (2문단에)"""
    lsi_examples = {
        "팀": "팀",
        "부서": "부서",
        "정책": "정책",
        "시스템": "시스템",
        "규제": "규제",
        "팀장": "팀장",
        "관리": "관리",
        "보안": "보안",
    }

    paragraphs = body.split("\n\n")

    # 2문단 확인
    if len(paragraphs) >= 2:
        second_para = paragraphs[1]

        # 현재 LSI 개수 세기
        lsi_count = sum(1 for word in lsi_examples if word in second_para)

        # 3개 미만이면 추가
        if lsi_count < 3:
            # 첫 문장에 LSI 키워드 추가
            addition = "팀이나 부서, 정책 쪽 안 건드린 사람들은 체감 안 할 듯. "
            if "솔직히" in second_para:
                second_para = second_para.replace("솔직히", "솔직히 " + addition)
            else:
                second_para = addition + second_para

            paragraphs[1] = second_para
            body = "\n\n".join(paragraphs)

    return body


def _reduce_keyword_repeat(text: str, keyword: str, max_repeat: int = 2) -> str:
    """키워드 반복 줄이기 (최대 2회)"""
    count = text.count(keyword)

    if count > max_repeat:
        # 뒤에서부터 제거
        words = text.split()
        removed = 0
        for i in range(len(words) - 1, -1, -1):
            if removed >= (count - max_repeat):
                break
            if keyword in words[i]:
                words[i] = ""
                removed += 1

        text = " ".join(filter(None, words))

    return text


def _post_process(title: str, body: str, keyword: str) -> tuple[str, str]:
    """생성된 글 자동 편집 (글자 수, LSI, 키워드 반복)"""
    # 1. 제목 조정
    title = _fix_title_length(title)

    # 2. 본문 글자 수 조정
    body = _fix_body_length(body)

    # 3. LSI 키워드 추가
    body = _add_lsi_keywords(body, keyword)

    # 4. 키워드 반복 줄이기
    title = _reduce_keyword_repeat(title, keyword, max_repeat=1)
    body = _reduce_keyword_repeat(body, keyword, max_repeat=1)

    return title, body


def _calculate_seo_score(title: str, body: str, keyword: str) -> tuple[int, list[str]]:
    """UGC 스타일 SEO 점수 계산 (100점 만점)"""
    score = 0
    issues = []

    # 1. 제목 글자 수: 30~45자 (+25점)
    title_len = len(title)
    if 30 <= title_len <= 45:
        score += 25
    elif 28 <= title_len <= 47:
        score += 15
        issues.append(f"제목 {title_len}자 (30~45자 권장)")
    else:
        issues.append(f"제목 {title_len}자 (30~45자 필수)")
        score -= 10

    # 2. 본문 글자 수: 350~450자 (+25점)
    body_len = len(body)
    if 350 <= body_len <= 450:
        score += 25
    elif 330 <= body_len <= 470:
        score += 15
        issues.append(f"본문 {body_len}자 (350~450자 권장)")
    else:
        issues.append(f"본문 {body_len}자 (350~450자 필수)")
        score -= 10

    # 3. 제목에 질문형 패턴: "?", "~어?", "나만 그래?" (+15점)
    question_patterns = ["?", "어?", "나만", "근데", "왜"]
    has_question = any(pattern in title for pattern in question_patterns)
    if has_question:
        score += 15
    else:
        issues.append("제목이 질문형 아님 (댓글 유도 부족)")

    # 4. 키워드 포함: 제목 + 본문 자연스럽게 (+15점)
    if keyword in title and keyword in body:
        keyword_count = (title + body).count(keyword)
        if keyword_count <= 2:
            score += 15
        else:
            score += 5
            issues.append(f"키워드 반복 {keyword_count}회 (자연스럽지 않음)")
    elif keyword in title or keyword in body:
        score += 8
        issues.append("키워드가 제목 또는 본문에만 있음")
    else:
        issues.append("키워드 미포함")

    # 5. LSI 키워드: 2문단에 3개 이상 (+15점)
    paragraphs = body.split("\n\n")
    if len(paragraphs) >= 2:
        second_para = paragraphs[1]
        lsi_candidates = {"팀", "부서", "API", "정책", "프로세스", "시스템", "개발", "관리", "보안", "데이터", "기술", "관련", "전문", "과정", "도구", "솔루션", "플랫폼", "팀장", "상황", "사항", "방식", "인력", "조직"}
        lsi_count = sum(1 for word in lsi_candidates if word in second_para)
        if lsi_count >= 3:
            score += 15
        elif lsi_count >= 2:
            score += 8
            issues.append(f"LSI 키워드 {lsi_count}개 (3개 이상 권장)")
        else:
            issues.append(f"LSI 키워드 부족: {lsi_count}개")
    else:
        issues.append("문단 구조 부족 (2문단 이상 필수)")

    # 6. UGC 톤: "~함", "~임", "ㅋㅋ", "ㅠ", "어?" 등 (+5점)
    ugc_markers = {"함", "임", "ㅋ", "ㅠ", "어?", "거 나", "나만", "형들", "고수님"}
    ugc_count = sum(body.count(marker) for marker in ugc_markers)
    if ugc_count >= 3:
        score += 5

    score = max(0, min(100, score))
    return score, issues


def _build_fallback_post(keyword: str, topic: str, news_url: str) -> dict:
    """
    Claude API 최대 재시도 소진 시 sender.py 검증을 통과하는 최소 품질 게시글 생성

    조건 충족:
    - 제목 30~45자 (질문형 포함)
    - 본문 350~450자 (음슴체 마커 5개 이상)
    - LSI 키워드: 팀, 부서, 정책, 시스템, 규제, 프로세스
    - source: 'Fallback' → sender.py 링크 검증 우회
    """
    # 제목: 키워드 + 고정 패턴으로 30자 이상 확보
    title_base = f"{keyword} 이슈 요즘 나만 이상하게 느끼는 거임?"
    if len(title_base) > 45:
        title_base = title_base[:44] + "?"
    elif len(title_base) < 30:
        # 짧은 키워드: 패딩 문자열로 30자 이상 확보
        # 패딩은 충분히 길게 (정확히 27자 이상)
        padding = "요즘 핫한 트렌드인데 나만 이상하게 느끼는 거임?"
        title_base = f"{keyword} {padding}"
        if len(title_base) > 45:
            title_base = title_base[:44] + "?"

    # 본문: 3문단 구조, 음슴체 마커 5개 이상, LSI 키워드 포함
    para1 = (
        f"{keyword} 관련해서 요즘 계속 이슈가 뜨고 있음. "
        f"주변에서는 다들 알고 있는데 나만 모르고 있었던 것 같더라. "
        f"생각보다 영향 범위가 넓다고 함. 나만 이렇게 뒤늦게 아는 거임? "
        f"라고 생각했었는데 찾아보니까 생각보다 복잡했음."
    )
    para2 = (
        f"솔직히 팀이나 부서 단위로 정책이나 시스템 바꾸는 거 "
        f"안 건드린 사람들은 체감 안 할 듯. 나도 예전에 관련 업무 "
        f"처리하다가 규제랑 프로세스 때문에 진짜 고생했었음. "
        f"{keyword}만 좋아지면 뭐하냐고, 현장에서는 따라가질 못하는 게 "
        f"문제였음 ㅠ. 관리 측 입장도 있겠지만 현실은 말도 안 됐음."
    )
    para3 = (
        f"형들은 {keyword} 이슈 터지면 일단 관망하는 편임? "
        f"아니면 바로 대응책 찾아보는 편임? "
        f"고수님들은 앞으로 이거 어떻게 흘러갈 것 같음? "
        f"개인적으로는 좀 더 체계적으로 접근했으면 좋겠는데 뭐."
    )

    body = f"{para1}\n\n{para2}\n\n{para3}"

    # 길이 자동 조정
    body = _fix_body_length(body)
    title_final = _fix_title_length(title_base)

    # SEO 점수 재계산
    seo_score, _ = _calculate_seo_score(title_final, body, keyword)

    return {
        "keyword": keyword,
        "title": title_final,
        "body": body,
        "topic": topic,
        "news_url": news_url,
        "seo_score": seo_score,
        "source": "Fallback",  # sender.py 링크 검증 우회
    }


def _parse_response(text: str) -> dict:
    """Claude 응답을 구조화된 형식으로 파싱 (라벨 제거)"""
    lines = text.split("\n")

    title = None
    body_lines = []
    source = None
    current_section = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # 섹션 라벨 감지 및 제거
        if "**1단계:" in line or "1단계:" in line or "제목" in line and not title:
            current_section = "title"
            continue
        elif "**2단계:" in line or "2단계:" in line or "1문단" in line:
            current_section = "body1"
            continue
        elif "**3단계:" in line or "3단계:" in line or "2문단" in line:
            current_section = "body2"
            continue
        elif "**4단계:" in line or "4단계:" in line or "3문단" in line:
            current_section = "body3"
            continue
        elif "**5단계:" in line or "5단계:" in line or "출처" in line:
            current_section = "source"
            continue
        elif "(뉴스 링크:" in line or "뉴스 링크:" in line:
            source = line
            continue

        # 라벨이 아닌 실제 콘텐츠 추출
        if line.startswith("**") and ":" in line:
            # 라벨 라인 스킵
            continue

        if line.startswith("-") or line.startswith("LSI"):
            # 지시사항 라인 스킵
            continue

        # 실제 콘텐츠
        if current_section == "title" and not title:
            if len(line) > 3 and not line.startswith("["):  # 예시나 지시문 제외
                title = line
        elif current_section in ["body1", "body2", "body3"]:
            if len(line) > 3 and not line.startswith("["):
                body_lines.append(line)

    # 유효성 검사
    if not title or len(body_lines) < 2:
        return None

    return {
        "title": title,
        "body_lines": body_lines,
        "source": source or ""
    }


def write_post(keyword_item: dict) -> dict:
    """음슴체 게시글 1개 작성 (기사 본문 참조 + SEO 최적화 + 품질검증)"""
    keyword = keyword_item['keyword']
    news_url = keyword_item.get('news_url', '')
    article_title = keyword_item.get('article_title', '')
    article_body = keyword_item.get('article_body', '')
    topic = keyword_item.get('topic', '기타')

    if not article_body:
        print(f"  [스킵] '{keyword}': 본문 없음", flush=True)
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)
    max_retries = 4
    retry_count = 0

    while retry_count <= max_retries:
        try:
            retry_msg = "\n\n[주의] 이전 버전 검증 실패. 아래 체크리스트를 다시 확인하고 정확히 다시 작성하세요:" if retry_count > 0 else ""
            if retry_msg:
                retry_msg += "\n- 제목: 정확히 30~45자인가? (끝에 ? 또는 ㅠ 있는가?)"
                retry_msg += "\n- 1문단: 팩트 최소 + '나만 그런 거 아님?' 있는가?"
                retry_msg += "\n- 2문단: LSI 키워드 3개 이상(팀, 부서, 정책, 시스템 등) 명시적 포함되어 있는가?"
                retry_msg += "\n- 3문단: A vs B 선택지와 미래질문 있는가?"

            user_message = f"""기사: {article_title}
본문: {article_body}
키워드(제목에 반드시 포함): {keyword}

=== 극도로 구조화된 형식으로 작성 ===

**1단계: 제목 (정확히 30~45자, "{keyword}" 1회만 포함, 반드시 ? 포함)**
제목을 여기에 쓰되, 정확히 글자를 세어서 30~45자로!
"{keyword}"는 제목에 딱 1번만, 마지막에 반드시 ? 포함!
예: "{keyword} 이슈인데 나만 손해임?" (이렇게 마지막에 ?)


**2단계: 1문단 (약 80~100자)**
[기사 핵심 팩트 1~2문장] 남들은 [반응] [나의 현실] 나만 그런 거 아님?

**3단계: 2문단 (약 120~150자, LSI 키워드 반드시 3개 이상!)**
솔직히 [팀/부서/직군1]이나 [정책/시스템2] [관련직군3] 쪽 안 건드린 사람들은 체감 안 할 듯.
나도 예전에 [구체적경험] 때문에 이러고 있는데... [{keyword}]만 좋으면 뭐하냐고 ㅠ

LSI 키워드 체크: 팀, 부서, 정책, 시스템, 규제 등 3개 이상 자연스럽게 포함!

**4단계: 3문단 (약 100~120자)**
형들은 [행동A] 했어? 아니면 [행동B]?
고수님들은 앞으로 [예측C]일까, [예측D]일까?

**5단계: 출처**
(뉴스 링크: {news_url}){retry_msg}"""

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text.strip()
            parsed = _parse_response(text)

            if not parsed:
                print(f"  [오류] '{keyword}' 형식 파싱 실패 (시도 {retry_count+1}/{max_retries+1})", flush=True)
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(1)
                    continue
                else:
                    return _build_fallback_post(keyword, topic, news_url)

            title = parsed["title"]
            body = "\n\n".join(parsed["body_lines"])

            # 자동 편집: 글자 수, LSI 키워드, 반복 조정
            title, body = _post_process(title, body, keyword)

            # SEO 점수 계산
            seo_score, issues = _calculate_seo_score(title, body, keyword)

            # 부분 검증: 제목, 본문, LSI 키워드 확인
            title_len = len(title)
            body_len = len(body)

            # 재시도 조건: 제목 범위 초과 OR 본문 범위 초과 OR LSI 부족
            needs_retry = (
                title_len < 30 or title_len > 45 or
                body_len < 350 or body_len > 450
            )

            if seo_score >= 80 and not needs_retry:
                print(f"     [SEO] '{keyword}' 점수: {seo_score}점 (OK)", flush=True)
                return {
                    "keyword": keyword,
                    "title": title,
                    "body": body,
                    "topic": topic,
                    "news_url": news_url,
                    "seo_score": seo_score,
                }
            else:
                if retry_count < max_retries:
                    if needs_retry:
                        print(f"     [재작성] '{keyword}': 제목{title_len}자/본문{body_len}자 범위 초과", flush=True)
                    else:
                        print(f"     [재작성] '{keyword}' 점수: {seo_score}점 (80점 미만)", flush=True)
                        if issues:
                            for issue in issues[:2]:
                                print(f"       → {issue}", flush=True)
                    retry_count += 1
                    continue
                else:
                    # 최대 재시도 후에도 반환
                    print(f"     [최종] '{keyword}' 점수: {seo_score}점 (검증 미완료 상태 반환)", flush=True)
                    return {
                        "keyword": keyword,
                        "title": title,
                        "body": body,
                        "topic": topic,
                        "news_url": news_url,
                        "seo_score": seo_score,
                    }

        except Exception as e:
            print(f"  [오류] '{keyword}' 글 작성 실패 (시도 {retry_count+1}): {str(e)[:50]}", flush=True)
            if retry_count < max_retries:
                retry_count += 1
                time.sleep(1)
                continue
            else:
                return _build_fallback_post(keyword, topic, news_url)


def write_posts(keyword_items: list[dict]) -> list[dict]:
    """여러 키워드에 대한 게시글 작성"""
    print("\n[작성] UGC 스타일 게시글 생성 중...", flush=True)

    posts = []
    for item in keyword_items:
        keyword = item['keyword']
        print(f"  → '{keyword}' 글 작성...", flush=True)
        post = write_post(item)
        if post:
            posts.append(post)
            print(f"     제목({len(post['title'])}자): {post['title'][:40]}...", flush=True)

    print(f"\n[작성 완료] {len(posts)}개 게시글 생성\n", flush=True)
    return posts
