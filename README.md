# 트렌드봇 (Trendbot)

네이버 뉴스의 실시간 트렌드를 수집하여 UGC 스타일의 게시글을 자동 생성하고 텔레그램으로 발송하는 봇입니다.

## 🎯 기능

- ✅ **실시간 트렌드 수집**: 네이버 뉴스에서 핫한 키워드 자동 추출
- ✅ **AI 게시글 생성**: Claude로 2030 직장인 톤의 UGC 스타일 콘텐츠 작성
- ✅ **자동 검증**: 글자 수, 음슴체 톤, 링크 등 자동 검사
- ✅ **텔레그램 발송**: 검증 통과한 게시글 자동 발송
- ✅ **정치 필터링**: 정치 뉴스 자동 제외
- ✅ **분야 다양성**: 경제, 사회, IT, 연예, 스포츠 균형있게 수집

## 📋 요구사항

- Python 3.8+
- Anthropic API 키
- Telegram 봇 토큰

## 🚀 설치 및 실행

### 1️⃣ 준비

```bash
# 저장소 클론
git clone <repo-url>
cd trendbot

# 의존성 설치
pip install -r requirements.txt
```

### 2️⃣ 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env에 API 키 입력
# - ANTHROPIC_API_KEY: Claude API 키
# - TELEGRAM_TOKEN: Telegram 봇 토큰
# - TELEGRAM_CHAT_ID: 메시지를 받을 채팅 ID
```

### 3️⃣ 실행 - 2가지 방식

**방식 A: CLI로 제어 (권장)**
```bash
# 봇 시작 (백그라운드, 2시간마다 반복)
python trendbot_cli.py start

# 상태 확인
python trendbot_cli.py status

# 1회 테스트 실행
python trendbot_cli.py test

# 봇 중지
python trendbot_cli.py stop

# 도움말
python trendbot_cli.py help
```

**방식 B: 직접 실행**
```bash
# 1회만 실행 (테스트)
python main.py once

# 2시간마다 반복
python main.py

# 도움말
python main.py help
```

## 📂 디렉토리 구조

```
trendbot/
├── src/                 # 실행 코드
│   ├── main.py         # 메인 진입점
│   ├── scheduler.py    # 스케줄러
│   ├── collector.py    # 트렌드 수집 (RSS + 웹 크롤링)
│   ├── selector.py     # 키워드 선별
│   ├── writer.py       # 게시글 생성
│   └── sender.py       # 텔레그램 발송
├── tests/              # 테스트 파일
├── data/keywords/      # 사용된 키워드 기록
├── docs/               # 설계 문서
├── trendbot_cli.py     # CLI 제어 도구
├── requirements.txt    # 의존성
├── .env.example        # 설정 예시
└── .gitignore         # Git 무시 파일
```

## 🔧 설정

### API 키 발급

**Anthropic API:**
1. https://console.anthropic.com 방문
2. API 키 생성
3. `.env`에 입력

**Telegram 봇:**
1. Telegram에서 @BotFather 채팅
2. `/newbot` 입력하여 봇 생성
3. 받은 토큰을 `.env`에 입력
4. `@userinfobot`으로 채팅 ID 확인

## 📊 작동 원리

```
[1] 트렌드 수집
  ├─ RSS 피드 시도 (빠름)
  └─ RSS 실패 시 웹 크롤링 (안정성)

[2] 키워드 선별
  └─ 정치 제외, 분야별 3개 선택

[3] 게시글 생성
  └─ Claude로 UGC 스타일 작성

[4] 검증
  └─ 제목 30~45자, 본문 350~450자, 음슴체 확인

[5] 발송
  └─ 텔레그램으로 자동 전송
```

## 📝 검증 규칙

생성된 게시글은 다음 조건을 모두 충족해야 발송됩니다:

- ✅ 제목: 30~45자
- ✅ 본문: 350~450자
- ✅ 음슴체 톤: 최소 1개 이상 (함, 임, 어?, 거, 더라 등)
- ✅ 정치 키워드: 제외
- ✅ 링크: 유효한 뉴스 URL

검증 실패 시 Fallback 기본값으로 자동 보충합니다.

## 🛠️ 개발

### 주요 파일 설명

**collector.py** - 트렌드 수집
- RSS 피드로 빠른 수집
- RSS 실패 시 웹 크롤링 fallback
- 정치 필터링 2단계 (URL + 본문)

**writer.py** - 게시글 생성
- Claude Sonnet으로 UGC 스타일 작성
- 5단계 공식: 제목 → 1문단 → 2문단 → 3문단 → 출처
- LSI 키워드 자동 삽입

**sender.py** - 발송 및 검증
- 게시글 자동 검증
- 텔레그램 API로 발송
- 오류 자동 보고

## 📈 성능

- 실행 시간: ~3-5분 (수집, 생성, 검증, 발송)
- CPU 사용: ~20-30%
- 메모리: ~50-100MB
- 수집 성공률: ~95% (Fallback 포함)

## 🐛 문제 해결

**"ANTHROPIC_API_KEY 오류"**
- `.env` 파일에 올바른 API 키 입력

**"텔레그램 발송 실패"**
- TELEGRAM_TOKEN과 CHAT_ID 확인
- 봇이 채팅에 초대되어 있는지 확인

**"키워드 수집 실패"**
- 인터넷 연결 확인
- 네이버 뉴스 접근 가능 여부 확인
- Fallback 기본값으로 자동 보충

## 📚 추가 자료

- [수집 로직 상세 검토](docs/COLLECTOR_REVIEW.md)
- [UGC 작성 전략](docs/UGC_REWRITE_STRATEGY.md)
- [롱테일 전략](docs/LONGTAIL_STRATEGY.md)
- [정치 필터링](docs/POLITICS_FILTER_STRATEGY.md)

## 📄 라이선스

MIT License

## 👨‍💻 기여

버그 리포트, 제안, Pull Request는 언제든 환영합니다!
