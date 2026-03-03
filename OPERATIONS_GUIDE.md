# 트렌드봇 운영 가이드

> 트렌드봇 실운영을 위한 설정, 실행, 모니터링, 문제해결 가이드

---

## 📋 목차

1. [초기 설정](#초기-설정)
2. [실행 방법](#실행-방법)
3. [모니터링](#모니터링)
4. [문제해결](#문제해결)
5. [로그 분석](#로그-분석)
6. [백업 및 유지보수](#백업-및-유지보수)

---

## 초기 설정

### 1단계: 환경 파일 설정

```bash
# .env 파일 생성 (또는 .env.example 복사)
cp .env.example .env

# 텍스트 에디터로 .env 열기
nano .env  # 또는 vim, code 등
```

### 2단계: API 키 설정

```env
# .env 파일 내용
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx    # Claude API 키
TELEGRAM_TOKEN=123456789:ABCdefGHIjklmn   # 텔레그램 봇 토큰
TELEGRAM_CHAT_ID=-123456789                # 텔레그램 채팅 ID
```

**API 키 얻는 방법:**

1. **Claude API 키** → https://console.anthropic.com
2. **텔레그램 토큰** → @BotFather 채팅 (Telegram)
   ```
   /start
   /newbot
   → 토큰 발급
   ```
3. **텔레그램 채팅 ID**
   ```bash
   # @userinfobot 채팅 후 ID 확인 또는
   # 봇에 메시지 보낸 후 API로 조회
   curl https://api.telegram.org/bot{TOKEN}/getUpdates
   ```

### 3단계: 의존성 설치

```bash
pip install -r requirements.txt
```

**주요 의존성:**
- `anthropic>=0.20` — Claude API
- `requests` — HTTP 통신
- `beautifulsoup4` — HTML 파싱
- `feedparser` — RSS 피드
- `schedule` — 2시간 주기 실행

---

## 실행 방법

### 옵션 1: 즉시 1회 실행 (테스트용)

```bash
python main.py once
```

**사용 시기:**
- 초기 설정 테스트
- API 키 유효성 검증
- 최신 결과 확인
- 새로운 기능 테스트

**예상 소요 시간:** 1~2분

**성공 로그:**
```
============================================================
트렌드봇 사이클 시작
============================================================
[수집] 키워드 수집 중...
[선별] 키워드 선별 중...
[작성] UGC 스타일 게시글 생성 중...
[검증] 규칙 준수 여부 확인 중...
[발송] 텔레그램 메시지 생성 중...
============================================================
[완료] 사이클 완료 (텔레그램 발송 완료)
============================================================
```

---

### 옵션 2: 스케줄러 모드 (정기 운영)

```bash
python main.py run
```

**동작:**
- 즉시 1회 실행
- 2시간마다 자동 반복
- 09:00~21:59 범위만 작동 (그 외 시간 스킵)
- Ctrl+C로 중단 가능

**백그라운드 실행 (권장):**

#### Windows (cmd)
```bash
# 새 cmd 창에서 실행
start "" python main.py run

# 또는 Task Scheduler에 등록 (아래 참조)
```

#### Linux/macOS (nohup)
```bash
nohup python main.py run > trendbot.log 2>&1 &
```

#### Linux/macOS (tmux)
```bash
tmux new-session -d -s trendbot "python main.py run"
tmux attach -t trendbot  # 어느 때든 로그 확인 가능
```

---

### Windows Task Scheduler 등록

1. **작업 스케줄러 열기**
   ```
   Win+R → taskschd.msc → Enter
   ```

2. **새 작업 만들기 (오른쪽 패널)**
   ```
   이름: TrendBot Auto Execution
   ```

3. **트리거 탭**
   - 작업 시작: 프로그램 시작 시
   - (또는) 시간 기반으로 09:00에 시작

4. **동작 탭**
   - 프로그램/스크립트: `python.exe`
   - 인수 추가: `C:\경로\main.py run`
   - 시작 위치: `C:\경로\`

5. **조건/설정 탭**
   - 작업 실패 시 재시도 활성화
   - 전원 설정 조정

---

## 모니터링

### 1. 실시간 로그 확인

```bash
# 전체 로그 보기
python main.py once

# 또는 파일로 저장
python main.py once > logfile_$(date +%Y%m%d_%H%M%S).log
```

### 2. used_keywords.json 확인

```bash
# 사용된 키워드 목록 확인
cat src/used_keywords.json

# 또는 Python으로 보기
python -m json.tool src/used_keywords.json | head -50
```

**정상 상태:**
- 파일 크기: 1~2KB
- 항목 수: 10~20개 (24시간 기준)
- 타임스탬프: 최근 날짜

---

### 3. 텔레그램 확인

**봇이 메시지를 보냈는지 확인:**
1. 텔레그램 채팅 확인
2. 메시지 형식:
   ```
   [트렌드봇] 2026-03-03 15:12

   1. <키워드> [분야]
   제목...
   본문...
   https://...
   ```

**에러 메시지 수신:**
```
⚠️ [트렌드봇 오류]
단계: 키워드 수집
오류: Connection timeout
```
→ 네트워크 문제 또는 API 오류

---

## 문제해결

### 1. "TELEGRAM_TOKEN/CHAT_ID 미설정" 에러

```
[경고] TELEGRAM_TOKEN/CHAT_ID 미설정. 발송 스킵.
```

**해결:**
```bash
# .env 파일 확인
cat .env | grep TELEGRAM

# 비어있으면 값 입력
nano .env
# TELEGRAM_TOKEN=... 입력
# TELEGRAM_CHAT_ID=... 입력
```

---

### 2. "ANTHROPIC_API_KEY 유효하지 않음" 에러

```
[오류] API 키 인증 실패
```

**해결:**
```bash
# API 키 유효성 확인
curl -H "x-api-key: {KEY}" https://api.anthropic.com/v1/messages

# 새 키 발급 → https://console.anthropic.com
# .env 업데이트
nano .env
```

---

### 3. "3개 미만 게시글 생성" 경고

```
[경고] 수집 부족 (1개). 최소 Fallback 추가...
```

**원인:**
- 네이버 뉴스 접근 불가
- 모든 기사가 정치 관련
- 크롤링 차단

**해결:**
```bash
# 1. 네트워크 확인
ping news.naver.com

# 2. 즉시 재시도
python main.py once

# 3. 다시 시도해도 실패 시 → 수동 조사 필요
```

---

### 4. "음슴체 마커 부족" 검증 실패

```
[검증 실패]
- [음슴체] 음슴체 마커 부족
```

**원인:**
- Claude AI가 음슴체 톤으로 작성 안 함
- Fallback 게시글 품질 문제

**자동 해결:**
- 5회 재시도 후 자동 Fallback 생성
- Fallback은 음슴체 마커 5개 이상 포함

---

### 5. "기사 링크 없음" 검증 실패

```
[검증 실패]
- [링크] 기사 링크 없음
```

**원인:**
- 본문 추출 실패 (타임아웃 등)
- Fallback 게시글 (링크 검증 우회됨)

**정상:**
- Fallback은 링크 검증 스킵 (자동 우회)

---

## 로그 분석

### 주요 로그 패턴

| 로그 | 의미 | 조치 |
|------|------|------|
| `[수집] RSS 피드: 0개 키워드` | RSS 차단됨 (정상) | 웹 크롤링으로 자동 전환 |
| `[본문] 본문 추출 실패` | 기사 URL 접근 불가 | 제목으로 대체 (정상) |
| `[재시도] SEO 점수 낮음` | 재작성 필요 | 최대 4회 재시도 |
| `[최종] 점수 미완료 상태 반환` | 5회 재시도 소진 | Fallback 사용 |
| `[검증 완료]` | 모든 검증 통과 | ✅ 정상 |
| `[검증 실패]` | 규칙 위반 | ❌ 발송 안 됨 |

---

### 성공적인 사이클 로그 예시

```
============================================================
트렌드봇 사이클 시작
============================================================

[트렌드봇] 뉴스 트렌드 수집 시작

  [수집] 네이버 RSS 피드 조회 중...
  [RSS 수집: 0개]
  [대체] RSS 수집 실패. 웹 크롤링으로 대체합니다.
  [수집] 네이버 뉴스 웹 크롤링 중...
  [수집] 웹 크롤링: 427개 기사 수집
  [본문] '키워드1' 500자 추출
  [본문] '키워드2' 350자 추출
  [수집] 유효 키워드: 3개 (분야: 3개)

[수집 완료] 총 3개 키워드

[선별] 키워드 선별 중...
  [선별] 선정된 키워드: 키워드1[IT], 키워드2[경제], 키워드3[사회]

[작성] UGC 스타일 게시글 생성 중...
  → '키워드1' 글 작성...
     [SEO] '키워드1' 점수: 95점 (OK)
  → '키워드2' 글 작성...
     [SEO] '키워드2' 점수: 88점 (OK)
  → '키워드3' 글 작성...
     [SEO] '키워드3' 점수: 91점 (OK)

[작성 완료] 3개 게시글 생성

[검증] 규칙 준수 여부 확인 중...
  [검증 완료] 모든 규칙 준수

[발송] 텔레그램 메시지 생성 중...
  → 3개 게시글 메시지 준비 완료
  [발송 완료] 텔레그램으로 전송됨

[기록] 3개 키워드 사용 기록 (총 21개 보관)

============================================================
[완료] 사이클 완료 (텔레그램 발송 완료)
============================================================
```

---

## 백업 및 유지보수

### 1. 정기 백업

```bash
# used_keywords.json 백업 (매주)
cp src/used_keywords.json backup/used_keywords_$(date +%Y%m%d).json

# 전체 코드 백업 (매달)
tar -czf trendbot_backup_$(date +%Y%m%d).tar.gz .
```

### 2. 로그 정리

```bash
# 30일 이상 된 로그 삭제
find . -name "*.log" -mtime +30 -delete

# 또는 수동으로
rm -f old_logs/*
```

### 3. 의존성 업데이트

```bash
# 의존성 최신 버전 확인
pip list --outdated

# 특정 패키지 업데이트
pip install --upgrade anthropic requests beautifulsoup4

# 또는 전체 업데이트
pip install --upgrade -r requirements.txt
```

---

### 4. 성능 최적화

**메모리 절감:**
```python
# collector.py 최상위
articles = articles[:30]  # 상위 30개만 검토
```

**API 비용 절감:**
```python
# writer.py
max_retries = 4  # 총 5회 시도 (과도한 재시도 방지)
```

---

## 유용한 명령어

### 빠른 테스트 (모든 단계 확인)
```bash
python main.py once
```

### 특정 단계만 테스트
```bash
# Python REPL에서
from src.collector import collect_all_trends
from src.selector import select_keywords
from src.writer import write_posts

keywords = collect_all_trends()      # 수집
selected = select_keywords(keywords) # 선별
posts = write_posts(selected)        # 생성
```

### 시스템 정보 확인
```bash
# Python 버전
python --version

# 설치된 패키지 확인
pip list | grep -E "anthropic|requests|schedule"

# 현재 시간 (09:00~21:59 운영 시간 확인)
date
```

### 네트워크 진단
```bash
# 네이버 뉴스 접근 가능 여부
curl -I https://news.naver.com

# Anthropic API 접근 가능 여부
curl -I https://api.anthropic.com

# 텔레그램 API 접근 가능 여부
curl -I https://api.telegram.org
```

---

## 긴급 대응

### 봇이 멈춘 경우

```bash
# 1. 프로세스 확인
ps aux | grep "python main.py"

# 2. 프로세스 중단
kill -9 <PID>

# 3. 다시 시작
python main.py run
```

### 에러 메시지 수신 중인 경우

```bash
# 1. 즉시 로그 확인
python main.py once

# 2. 에러 내용 기록
# → 아래 [지원 요청](#지원-요청) 참조
```

### 데이터 손상 시

```bash
# used_keywords.json 초기화 (모든 키워드 해제)
echo "[]" > src/used_keywords.json

# 주의: 동일 키워드 재사용 가능해짐
```

---

## 지원 요청

문제 발생 시 다음 정보를 수집하세요:

1. **로그 출력:**
   ```bash
   python main.py once > error_log.txt 2>&1
   ```

2. **환경 정보:**
   ```bash
   python --version
   pip list | grep anthropic
   ```

3. **설정 확인 (민감정보 제외):**
   ```bash
   cat .env | grep -v "KEY\|TOKEN"  # API 키는 제외
   ```

4. **전송:**
   - GitHub Issues 또는
   - 이메일: [지원 이메일]

---

## 참고 링크

- **BOT_SPEC.md** — 봇 명세서 및 기술 문서
- **Anthropic API Docs** — https://docs.anthropic.com
- **Telegram Bot API** — https://core.telegram.org/bots/api
- **Python Schedule** — https://schedule.readthedocs.io
