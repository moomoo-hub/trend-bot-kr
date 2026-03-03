# 트렌드봇 배포 옵션 비교 가이드

> 로컬, CE2, EC2 등 다양한 환경에서의 배포 비교 및 선택 가이드

---

## 배포 옵션 요약

| 항목 | 로컬 (개발) | CE2 | AWS EC2 |
|------|-----------|-----|---------|
| **초기 설정 난이도** | ★☆☆ (쉬움) | ★★☆ (중간) | ★★★ (어려움) |
| **월간 비용** | $0 | ~$8-20 | ~$11 (프리 티어) |
| **24/7 운영** | ❌ | ✅ | ✅ |
| **관리 난이도** | ★☆☆ (낮음) | ★★☆ (중간) | ★★☆ (중간) |
| **확장성** | ❌ | 제한적 | ✅ (높음) |
| **학습곡선** | ★☆ (낮음) | ★★ (중간) | ★★★ (높음) |

---

## 상황별 추천 배포

### 1️⃣ 개발/테스트 단계

**추천: 로컬 환경**

```bash
# 로컬에서 한 번에 실행
python main.py once

# 또는 스케줄러 테스트
python main.py run
```

**장점:**
- 즉시 실행 가능
- 로그 실시간 확인 용이
- 개발 변경사항 즉시 테스트

**단점:**
- 컴퓨터 켜져있어야 함
- 24/7 운영 불가능

---

### 2️⃣ 초기 운영 단계 (안정성 검증)

**추천: CE2 (또는 가정용 NAS/라즈베리파이)**

```bash
# CE2에 배포
git clone https://github.com/moomoo-hub/trend-bot-kr.git
cd trend-bot-kr
pip install -r requirements.txt

# .env 설정
nano .env

# 테스트 실행
python main.py once

# 백그라운드 실행
nohup python main.py run > trendbot.log 2>&1 &
```

**장점:**
- 저렴한 비용
- 제어 용이
- 로그 확인 편함
- 이미 운영 중인 서버 활용

**단점:**
- 24/7 안정성 의존도 있음
- 서버 리소스 공유
- 제한된 확장성

**CE2가 이미 있다면 가장 경제적**

---

### 3️⃣ 장기 안정 운영 (권장)

**추천: AWS EC2**

```bash
# EC2 배포 (상세 가이드: EC2_DEPLOYMENT.md)
ssh -i trendbot-key.pem ubuntu@<IP>
git clone https://github.com/moomoo-hub/trend-bot-kr.git
cd trend-bot-kr
source venv/bin/activate
pip install -r requirements.txt

# cron으로 자동 실행
crontab -e
# 0 9,11,13,15,17,19,21 * * * ... (2시간 간격)
```

**장점:**
- 높은 가용성 (99.9% uptime)
- AWS 관리형 서비스
- 프리 티어로 첫 1년 무료
- 전문적 모니터링 가능
- 확장성 우수
- 정부/기업 신뢰도

**단점:**
- 학습곡선 높음
- AWS 계정 필요
- 이후 요금 발생 가능

---

## 각 배포 방식별 상세 가이드

### 📌 로컬 환경 배포 (Windows/Mac/Linux)

**파일:** OPERATIONS_GUIDE.md 참조

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 설정
# .env 파일 생성 (API 키 입력)

# 3. 테스트 실행
python main.py once

# 4. 정기 실행 (컴퓨터 켜져있을 때)
python main.py run
```

**운영 환경:**
- 개인 노트북/데스크톱
- 항상 켜져 있어야 함
- 네트워크 끊김 주의

---

### 📌 CE2 배포 (기존 서버 활용)

**가정:** 집이나 사무실에 운영 중인 서버/NAS가 있음

```bash
# 1. 코드 다운로드
git clone https://github.com/moomoo-hub/trend-bot-kr.git
cd trend-bot-kr

# 2. 가상 환경 (선택사항)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. .env 설정
nano .env  # 또는 에디터로 생성

# 5. 백그라운드 실행
# Linux/Mac (nohup 사용)
nohup python main.py run > trendbot.log 2>&1 &

# 또는 screen/tmux 사용
screen -S trendbot
python main.py run
# Ctrl+A → D (detach)

# 또는 Windows Task Scheduler (OPERATIONS_GUIDE.md 참조)
```

**모니터링:**
```bash
# 프로세스 확인
ps aux | grep main.py

# 로그 확인
tail -f trendbot.log

# 중단
kill -9 <PID>
```

**장점:**
- 기존 서버 활용 (비용 절감)
- 물리적 접근 가능
- 트러블슈팅 용이

**단점:**
- 서버 안정성에 의존
- 수동 재시작 필요할 수 있음

---

### 📌 EC2 배포 (완전 관리형)

**파일:** EC2_DEPLOYMENT.md 참조

```bash
# 1. AWS 계정 생성 → https://aws.amazon.com

# 2. EC2 인스턴스 생성
# - AMI: Ubuntu 24.04 LTS
# - 타입: t2.micro (프리 티어)
# - 스토리지: 30GB

# 3. SSH 접속
ssh -i trendbot-key.pem ubuntu@<PUBLIC_IP>

# 4. 환경 설정 (EC2_DEPLOYMENT.md의 "환경 구성" 섹션)
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip git -y

# 5. 코드 배포
git clone https://github.com/moomoo-hub/trend-bot-kr.git
cd trend-bot-kr

# 6. 가상 환경
python3 -m venv venv
source venv/bin/activate

# 7. 의존성 설치
pip install -r requirements.txt

# 8. 환경 설정
nano .env

# 9. 자동 실행 (cron)
crontab -e
# 추가:
# 0 9,11,13,15,17,19,21 * * * cd ~/trend-bot-kr && source venv/bin/activate && python main.py once >> ~/trendbot.log 2>&1
```

**모니터링:**
```bash
# 로그 확인
tail -f ~/trendbot.log

# cron 작업 확인
crontab -l

# 시스템 로그
sudo journalctl -xn
```

**비용:**
- 프리 티어: 무료 (12개월, t2.micro)
- 이후: ~$11/월 (또는 예약 인스턴스로 절감)

---

## 배포 선택 의사결정 트리

```
┌─ 트렌드봇을 어디에 배포할까?
│
├─ 개발/테스트 중? → 로컬 환경
│  └─ 이유: 즉시 실행, 수정 간편
│
├─ 기존 서버/CE2 있음? → CE2 배포
│  └─ 장점: 저비용, 기존 자산 활용
│  └─ 단점: 서버 안정성 의존
│
├─ 장기 안정 운영 필요? → AWS EC2
│  ├─ AWS 계정 있음? → EC2 배포
│  │  └─ 프리 티어 적용 가능
│  │
│  └─ AWS 계정 없음?
│     ├─ 아마존 가입 전 검토: https://aws.amazon.com/free
│     └─ 프리 티어 = 12개월 무료 + t2.micro 무제한
│
└─ 확실하지 않음? → CE2로 시작 → 필요시 EC2로 마이그레이션
```

---

## 현재 상황별 추천

### 💡 최적 시나리오 1: "일단 해보자"

1. **로컬에서 테스트**
   ```bash
   python main.py once  # 1~2분
   ```

2. **테스트 성공 후 CE2 배포** (이미 있다면)
   ```bash
   # 백그라운드 실행
   nohup python main.py run > trendbot.log 2>&1 &
   ```

3. **1주일 안정성 확인 후 EC2 이전** (필요시)

---

### 💡 최적 시나리오 2: "장기 안정 운영"

1. **곧바로 AWS EC2 배포**
   ```bash
   # EC2_DEPLOYMENT.md 따라가기
   # 프리 티어로 12개월 무료
   ```

2. **cron으로 자동 실행 설정**
   ```bash
   crontab -e
   ```

3. **CloudWatch로 모니터링**

---

## 마이그레이션 경로

### 로컬 → CE2

```bash
# 1. CE2에서 코드 다운로드
git clone https://github.com/moomoo-hub/trend-bot-kr.git

# 2. 로컬에서 used_keywords.json 복사 (선택)
scp -r ~/trend-bot-kr/src/used_keywords.json user@ce2:/home/trend-bot-kr/src/

# 3. CE2에서 백그라운드 실행
nohup python main.py run > trendbot.log 2>&1 &
```

### CE2 → EC2

```bash
# 1. EC2 인스턴스 생성 (EC2_DEPLOYMENT.md)

# 2. EC2에서 코드 다운로드
git clone https://github.com/moomoo-hub/trend-bot-kr.git

# 3. CE2에서 used_keywords.json 백업
scp -r user@ce2:/path/used_keywords.json ~/backup/

# 4. EC2에 전송 (선택)
scp -r ~/backup/used_keywords.json ubuntu@<EC2_IP>:~/trend-bot-kr/src/

# 5. EC2에서 cron 설정
crontab -e
```

---

## 비용 비교 (월단위)

```
로컬 (윈도우/맥):
- 전기료: ~$3-5/월 (하드웨어 사용)
- 네트워크: 포함
└─ 총: ~$3-5

CE2 (기존 서버 활용):
- 초기 투자: $50-500 (1회, 서버 구매)
- 월간 유지: $1-5 (전기료만)
└─ 총: ~$1-5/월

AWS EC2 (프리 티어):
- 12개월: $0 (t2.micro)
- 이후: ~$11/월 (t2.micro 계속 사용 시)
└─ 총: $0 (첫 1년), 그 후 ~$11

AWS EC2 (예약 인스턴스):
- 1년 약정: ~$60 (월 $5, 30% 절감)
- 3년 약정: ~$150 (월 $4, 50% 절감)
└─ 총: ~$5-4/월
```

---

## 결론

| 상황 | 추천 | 이유 |
|------|------|------|
| **개발 중** | 로컬 | 빠른 테스트 |
| **초기 검증** | 로컬 또는 CE2 | 비용 최소 |
| **정기 운영** | CE2 | 기존 자산 활용 |
| **장기 안정** | EC2 | 높은 가용성 + 프리 티어 |
| **대규모 확장** | EC2 + RDS/S3 | AWS 생태계 활용 |

**지금 바로 시작:**
1. 로컬에서 `python main.py once` 한 번 실행
2. 성공하면 CE2 또는 EC2에 배포
3. 1주 모니터링 후 정기 운영으로 전환

