#!/usr/bin/env python
"""
검증 규칙을 통과하는 테스트 메시지 발송
"""
import os
import sys
from pathlib import Path

# src 폴더를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
import requests
from datetime import datetime

# 프로젝트 루트의 .env 파일 로드
root_dir = Path(__file__).parent.parent
load_dotenv(root_dir / ".env")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 검증 규칙에 맞춘 테스트 게시글들
test_posts = [
    {
        'keyword': '번아웃',
        'title': '회사에서 주말까지 번아웃 온다는데 나만 멀쩡한 거 아니야?',  # 43자
        'body': '''이번 뉴스에 따르면 직장인들의 번아웃이 심각하다고 함. 근데 정말 신기한데, 우리 팀도 퇴근 후 카톡이 자주 오는데도 불구하고 번아웃 증상을 안 보이는 팀원들이 있더라니까.

정신건강 전문가들이 말하는 번아웃의 원인은 과도한 업무와 관리 부족이라고 했는데, 개인적으로 본 바로는 좀 다른 것 같음. 팀장 성향도 중요하고, 부서 문화도 영향을 준다고 생각하는 거임. 내가 예전에 다니던 회사는 똑같이 업무량도 많고 규제도 많았지만, 팀 분위기가 좋아서 안 힘들었거든.

결국 내 생각에는 번아웃의 진짜 원인은 보상과 인정 부족 아닐까? 형들은 번아웃 극복하기 위해 이직이 답이라고 생각해? 아니면 현 회사에서 뭔가 바꿔보는 게 낫다고 생각해?''',  # 385자
        'topic': '사회',
        'news_url': 'https://n.news.naver.com/article/011/0004593554?ntype=RANKING'
    },
    {
        'keyword': '주식',
        'title': '코스피 3000선 넘겼는데 평민의 지갑은 언제 채워지냐?',  # 40자
        'body': '''어제 코스피가 3000을 넘겼다고 뉴스에서 난리였음. 근데 막상 주변 사람들이 돈을 번다는 얘기는 못 들었는데, 거 나만 그런 거임?

투자 유튜버들은 다들 수익률을 자랑하더라니까. 증시가 오르면 뭐가 달라진다는 건지 진짜 모르겠음. 내 동료들도 코스피 올라갔다고 해서 주식을 사봤는데, 자기 종목만 계속 떨어진대. 증권사 리포트도 읽어봤지만 무슨 말인지 모르겠고, 펀드도 추천받아봤지만 수수료만 나간다고 함.

결국 주식으로 돈을 번다는 게 금리를 이기는 거라는데, 나는 그냥 은행에 넣어뒀을 때가 더 나을 것 같음. 하지만 자산관리를 위해서는 뭔가는 해야 한다고 생각함. 형들은 코스피 3000 시대에 뭐에 투자하고 계셔? 아니면 그냥 현금 보유가 정답이라고 생각해?''',  # 413자
        'topic': '경제',
        'news_url': 'https://n.news.naver.com/article/025/0003505430?ntype=RANKING'
    },
    {
        'keyword': '드라마',
        'title': '넷플릭스 드라마 하나로 일주일을 버티고 있는 내가 이상한 거임?',  # 43자
        'body': '''이번 주 가장 재미있는 드라마가 나왔다고 함. 근데 요즘 드라마들이 죄다 15~17부작으로 길어지는 추세라더니. 내 기준에는 너무 길다고 생각함.

예능 컨텐츠들도 보면 기획이 자꾸 반복되는데, 드라마도 마찬가지인 것 같음. 같은 구성이 자꾸만 나오니까 중간에 흥미를 잃곤 함. 그런데도 불구하고 한 편을 또 본다고 했을 때, 배우 연기력이랑 스토리라인 구성이 되게 중요한 것 같음. 영상미도 예쁘면 좋지만, 결국 내용이 좋아야 중독적으로 보게 되더라.

최근에 본 드라마들 중에서 정말 볼 만한 게 별로 없어서 아쉬움. 하지만 봐도 너무 재밌으니까 계속 보게 되는 거고, 그래서 한 드라마로 일주일을 버티는 것 같음. 형들은 최근에 본 드라마 중 추천할 만한 게 있어? 아니면 영화나 예능을 보는 게 낫다고 생각해?''',  # 400자
        'topic': '연예',
        'news_url': 'https://n.news.naver.com/article/003/0013789800?ntype=RANKING'
    }
]

print("=" * 60)
print("테스트 메시지 검증 및 발송")
print("=" * 60)

# 각 게시글 검증
for i, post in enumerate(test_posts, 1):
    title_len = len(post['title'])
    body_len = len(post['body'])
    print(f"\n{i}. {post['keyword']} [{post['topic']}]")
    print(f"   제목: {title_len}자 {'OK' if 30 <= title_len <= 45 else 'FAIL (30~45자 필요)'}")
    print(f"   본문: {body_len}자 {'OK' if 350 <= body_len <= 450 else 'FAIL (350~450자 필요)'}")

    # 음슴체 확인
    markers = {"함", "임", "어?", "거", "더라", "다고", "수", "네"}
    onseumche_count = sum(post['body'].count(m) for m in markers)
    print(f"   음슴체: {onseumche_count}개 {'OK' if onseumche_count >= 1 else 'FAIL'}")

# 텔레그램 발송
if TOKEN and CHAT_ID:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"[트렌드봇] {now}\n\n"

    for i, post in enumerate(test_posts, 1):
        message += f"{i}. <b>{post['keyword']}</b> [{post['topic']}]\n"
        message += f"{post['title']}\n"
        message += f"{post['body']}\n"
        message += f"{post['news_url']}\n\n"

    print(f"\n{'='*60}")
    print("Sending to Telegram...")

    try:
        res = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)

        if res.status_code == 200:
            print("[SUCCESS] Message sent!")
        else:
            print(f"[FAILED] {res.status_code}")
            print(f"   {res.text}")
    except Exception as e:
        print(f"[ERROR] {e}")
else:
    print("\n[ERROR] TELEGRAM_TOKEN or CHAT_ID not set")
