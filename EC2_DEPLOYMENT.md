# EC2에 트렌드봇 배포 가이드

> AWS EC2 인스턴스에 트렌드봇을 배포하고 운영하는 완벽한 가이드

---

## 📋 목차

1. [AWS 계정 및 EC2 설정](#aws-계정-및-ec2-설정)
2. [EC2 인스턴스 생성](#ec2-인스턴스-생성)
3. [보안 그룹 설정](#보안-그룹-설정)
4. [인스턴스 연결](#인스턴스-연결)
5. [환경 구성](#환경-구성)
6. [트렌드봇 설치](#트렌드봇-설치)
7. [백그라운드 실행 설정 (cron)](#백그라운드-실행-설정-cron)
8. [모니터링 및 로그](#모니터링-및-로그)
9. [문제해결](#문제해결)
10. [비용 최적화](#비용-최적화)

---

## AWS 계정 및 EC2 설정

### 1단계: AWS 계정 생성

1. **AWS 콘솔 접속**
   - https://aws.amazon.com/ 방문
   - "AWS 계정 만들기" 클릭
   - 이메일, 패스워드, 결제 정보 입력

2. **프리 티어 확인**
   - 새 계정은 12개월 프리 티어 자격 (월 750시간 무료)
   - t2.micro 인스턴스 1개 운영 시 충분함

---

## EC2 인스턴스 생성

### 1단계: EC2 콘솔 열기

```
AWS 콘솔 → "EC2" 검색 → EC2 대시보드 클릭
```

### 2단계: 인스턴스 시작

1. **EC2 대시보드 → "인스턴스 시작" 버튼 클릭**

2. **AMI (이미지) 선택**
   ```
   Ubuntu Server 24.04 LTS
   (또는 Amazon Linux 2)
   → 선택
   ```

3. **인스턴스 타입 선택**
   ```
   t2.micro (프리 티어 사용 가능)
   CPU: 1 vCPU
   메모리: 1GB
   ```

4. **인스턴스 세부 정보 구성**
   - 네트워크: 기본 (VPC)
   - 퍼블릭 IP 활성화: ✅
   - IAM 역할: 기본값
   - 기타: 기본값으로 진행

5. **스토리지 추가**
   ```
   크기: 30GB (기본값)
   볼륨 타입: gp3 (또는 gp2)
   → 다음
   ```

6. **태그 추가** (선택사항)
   ```
   Key: Name
   Value: TrendBot
   ```

7. **보안 그룹 구성** → [다음 섹션](#보안-그룹-설정) 참조

8. **검토 및 시작**
   - 설정 확인 후 "인스턴스 시작" 클릭

### 3단계: 키 페어 생성

```
새 키 페어 생성
이름: trendbot-key (또는 원하는 이름)
타입: RSA
형식: .pem (Linux/Mac) 또는 .ppk (Windows PuTTY)
```

**⚠️ 중요:**
- 다운로드된 `.pem` 파일 안전히 보관
- 재다운로드 불가능하므로 잃어버리면 인스턴스 접속 불가

---

## 보안 그룹 설정

### 인바운드 규칙 (Inbound)

인스턴스 실행 중 → 인스턴스 선택 → "보안" 탭 → 보안 그룹 클릭

**필요한 규칙:**

| 타입 | 프로토콜 | 포트 | 소스 | 용도 |
|------|--------|------|------|------|
| SSH | TCP | 22 | 0.0.0.0/0 (또는 내IP) | 인스턴스 접속 |

**설정 방법:**
```
보안 그룹 → 인바운드 규칙 편집 → 규칙 추가
타입: SSH
프로토콜: TCP
포트 범위: 22
소스: 0.0.0.0/0 (모든 IP) 또는 내_IP/32 (더 안전)
→ 저장
```

### 아웃바운드 규칙 (Outbound)

기본값 (모든 트래픽 허용) 유지

---

## 인스턴스 연결

### Linux/Mac 사용자

```bash
# 1. .pem 파일 권한 변경 (필수)
chmod 400 ~/Downloads/trendbot-key.pem

# 2. 인스턴스의 퍼블릭 IP 확인
# AWS 콘솔 → EC2 → 인스턴스 → 퍼블릭 IPv4 주소 복사
# 예: 52.71.24.123

# 3. SSH 접속
ssh -i ~/Downloads/trendbot-key.pem ubuntu@52.71.24.123
```

**처음 접속 시 경고:**
```
Are you sure you want to continue connecting? (yes/no) yes
```

### Windows 사용자 (PuTTY)

1. **PuTTY 다운로드**: https://www.putty.org/

2. **키 변환** (.pem → .ppk)
   - PuTTYgen 실행
   - "Load" → trendbot-key.pem 선택
   - "Save private key" → trendbot-key.ppk 저장

3. **PuTTY로 접속**
   - Host: ubuntu@52.71.24.123 (또는 ec2-user@... for Amazon Linux)
   - Connection → SSH → Auth → Private key file: trendbot-key.ppk
   - "Open" 클릭

### Windows 사용자 (WSL2 또는 PowerShell)

```powershell
# WSL2 또는 Git Bash에서
ssh -i "C:\Users\YOUR_NAME\Downloads\trendbot-key.pem" ubuntu@52.71.24.123
```

---

## 환경 구성

EC2 인스턴스에 접속 후:

### 1단계: 시스템 업데이트

```bash
sudo apt update
sudo apt upgrade -y
```

### 2단계: Python 3.11+ 설치 (Ubuntu 기준)

```bash
# Python 설치
sudo apt install -y python3 python3-pip python3-venv

# 버전 확인
python3 --version  # 3.11 이상이어야 함
```

**Amazon Linux 2인 경우:**
```bash
sudo yum update -y
sudo yum install -y python3 python3-pip
```

### 3단계: 필수 시스템 라이브러리 설치

```bash
sudo apt install -y git curl wget build-essential
```

### 4단계: 시간대 설정

```bash
# 한국 시간대로 설정
sudo timedatectl set-timezone Asia/Seoul

# 확인
date
```

---

## 트렌드봇 설치

### 1단계: GitHub에서 코드 다운로드

```bash
# 홈 디렉토리로 이동
cd ~

# 레포지토리 클론
git clone https://github.com/moomoo-hub/trend-bot-kr.git

# 트렌드봇 디렉토리로 이동
cd trend-bot-kr
```

### 2단계: 가상 환경 생성 (권장)

```bash
# 가상 환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate

# 프롬프트가 (venv)로 변경되면 성공
```

### 3단계: 의존성 설치

```bash
pip install -r requirements.txt
```

### 4단계: 환경 변수 설정

```bash
# .env 파일 생성
nano .env
```

**입력 내용:**
```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
TELEGRAM_TOKEN=123456789:ABCdefGHIjklmn
TELEGRAM_CHAT_ID=-123456789
```

**저장:**
- Ctrl+O → Enter
- Ctrl+X

### 5단계: 초기 테스트

```bash
# 가상 환경 활성화 (위에서 했으면 스킵)
source venv/bin/activate

# 1회 실행 테스트
python main.py once

# 정상 동작 확인:
# - "[수집] ... 중" 로그 표시
# - "[작성] ... 중" 로그 표시
# - "[발송 완료] 텔레그램으로 전송됨" 메시지
```

**성공 로그 예:**
```
============================================================
트렌드봇 사이클 시작
============================================================
[수집] 네이버 뉴스 웹 크롤링 중...
[수집] 웹 크롤링: 427개 기사 수집
[작성] UGC 스타일 게시글 생성 중...
[검증] 규칙 준수 여부 확인 중...
[발송] 텔레그램 메시지 생성 중...
[발송 완료] 텔레그램으로 전송됨
============================================================
[완료] 사이클 완료 (텔레그램 발송 완료)
============================================================
```

---

## 백그라운드 실행 설정 (cron)

### 1단계: crontab 편집

```bash
crontab -e
```

**첫 실행 시 에디터 선택:**
```
Select an editor.  1. /bin/nano
                   2. /bin/vim.basic
                   3. /bin/vim

Choose 1-3: 1  (nano 권장)
```

### 2단계: cron 작업 추가

파일 하단에 추가:

```bash
# 매 2시간마다 실행 (09:00 ~ 21:59)
0 9,11,13,15,17,19,21 * * * cd ~/trend-bot-kr && source venv/bin/activate && python main.py once >> ~/trendbot.log 2>&1

# 또는 더 정확한 설정 (09:00, 11:00, 13:00, ... 21:00)
0 9 * * * cd ~/trend-bot-kr && source venv/bin/activate && python main.py once >> ~/trendbot.log 2>&1
0 11 * * * cd ~/trend-bot-kr && source venv/bin/activate && python main.py once >> ~/trendbot.log 2>&1
0 13 * * * cd ~/trend-bot-kr && source venv/bin/activate && python main.py once >> ~/trendbot.log 2>&1
0 15 * * * cd ~/trend-bot-kr && source venv/bin/activate && python main.py once >> ~/trendbot.log 2>&1
0 17 * * * cd ~/trend-bot-kr && source venv/bin/activate && python main.py once >> ~/trendbot.log 2>&1
0 19 * * * cd ~/trend-bot-kr && source venv/bin/activate && python main.py once >> ~/trendbot.log 2>&1
0 21 * * * cd ~/trend-bot-kr && source venv/bin/activate && python main.py once >> ~/trendbot.log 2>&1
```

**저장:**
- Ctrl+O → Enter
- Ctrl+X

### 3단계: cron 작업 확인

```bash
# 설정된 cron 작업 확인
crontab -l

# 로그 확인 (실시간)
tail -f ~/trendbot.log

# 또는 system 크론 로그 확인
sudo grep CRON /var/log/syslog | tail -20
```

### Cron 스케줄 설명

```
┌───────────── 분 (0-59)
│ ┌───────────── 시간 (0-23)
│ │ ┌───────────── 일 (1-31)
│ │ │ ┌───────────── 월 (1-12)
│ │ │ │ ┌───────────── 요일 (0-7, 0=일, 7=토)
│ │ │ │ │
│ │ │ │ │
* * * * *  실행할 명령

예제:
0 9 * * *  → 매일 09:00 실행
0 */2 * * * → 매 2시간 (00:00, 02:00, 04:00, ...)
0 9-21 * * * → 09:00~21:59 (매시간)
```

---

## 모니터링 및 로그

### 실시간 로그 확인

```bash
# 전체 로그 보기
tail -f ~/trendbot.log

# 마지막 100줄 보기
tail -100 ~/trendbot.log

# 특정 에러 찾기
grep "오류\|Error" ~/trendbot.log

# 로그 파일 크기 확인
ls -lh ~/trendbot.log
```

### 로그 정리

```bash
# 로그 파일 초기화 (크기 관리)
> ~/trendbot.log

# 또는 날짜별 로그 저장 후 초기화
cp ~/trendbot.log ~/trendbot_$(date +%Y%m%d).log
> ~/trendbot.log
```

### cron 시스템 로그 확인

```bash
# Linux cron 실행 기록
sudo tail -50 /var/log/syslog | grep CRON

# 또는 journalctl 사용
sudo journalctl -u cron --since "1 hour ago"
```

### 프로세스 상태 확인

```bash
# Python 프로세스 확인
ps aux | grep python

# 또는 더 간단히
pgrep -fa "main.py"
```

---

## 문제해결

### 1. 접속 불가 (Permission denied)

```bash
# .pem 파일 권한 확인
ls -la ~/Downloads/trendbot-key.pem

# 권한 설정
chmod 400 ~/Downloads/trendbot-key.pem
```

### 2. 가상 환경 활성화 불가

```bash
# 가상 환경 재생성
cd ~/trend-bot-kr
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. API 키 오류

```bash
# .env 파일 확인
cat ~/.trend-bot-kr/.env

# 혹은 nano로 수정
nano ~/trend-bot-kr/.env
```

### 4. Cron 작업이 실행되지 않음

```bash
# crontab 구문 검증
crontab -l

# 수동으로 한 번 테스트
cd ~/trend-bot-kr && source venv/bin/activate && python main.py once

# 시스템 로그 확인
sudo journalctl -xn
```

### 5. 디스크 부족

```bash
# 디스크 사용량 확인
df -h

# 로그 파일 크기 확인
du -sh ~/trendbot.log

# 로그 정리
> ~/trendbot.log
```

### 6. 메모리 부족

```bash
# 메모리 확인
free -h

# 프로세스별 메모리 확인
top -b -n 1 | head -20
```

---

## 비용 최적화

### 프리 티어 요금제 최대화

| 리소스 | 월간 무료 | 권장 사항 |
|--------|---------|---------|
| EC2 t2.micro | 750시간 | 항상 실행해도 무료 |
| EBS (SSD) | 30GB | 넉넉함 |
| 데이터 전송 | 1GB/월 | 트렌드봇은 100MB 미만 |

### 요금 예상

```
월간 예상 비용 (프리 티어 외):
- t2.micro (365일 24시간): $8.50
- EBS gp3 (30GB): $2.40
- 데이터 전송: ~$0.20
────────────────────────
총계: ~$11/월 (매우 저렴)
```

### 비용 절감 팁

1. **인스턴스 자동 중지 설정** (필요 없을 때)
   ```
   AWS 콘솔 → EC2 → 인스턴스 → 자동 시작/중지 설정
   ```

2. **예약 인스턴스** (1년 약정 시 약 30% 절감)
   ```
   AWS 콘솔 → 예약 인스턴스 → 구매
   ```

3. **비용 경보 설정**
   ```
   AWS 콘솔 → Billing → 요금 경보 → $20 초과 시 알림
   ```

---

## 고급 설정

### Systemd 서비스로 관리 (선택사항)

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/trendbot.service
```

**내용:**
```ini
[Unit]
Description=Trend Bot Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trend-bot-kr
ExecStart=/home/ubuntu/trend-bot-kr/venv/bin/python /home/ubuntu/trend-bot-kr/main.py run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**활성화:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable trendbot.service
sudo systemctl start trendbot.service
sudo systemctl status trendbot.service
```

### CloudWatch 로그 저장 (AWS 활용)

CloudWatch에 로그 자동 저장:
```bash
# CloudWatch Logs Agent 설치 및 설정
# (고급 설정이므로 필요 시 요청)
```

---

## 유용한 명령어 모음

```bash
# 인스턴스 접속
ssh -i ~/trendbot-key.pem ubuntu@<PUBLIC_IP>

# 가상 환경 활성화
source ~/trend-bot-kr/venv/bin/activate

# 트렌드봇 1회 실행
python ~/trend-bot-kr/main.py once

# 로그 실시간 확인
tail -f ~/trendbot.log

# cron 작업 조회
crontab -l

# 프로세스 모니터링
ps aux | grep main.py

# 디스크 사용량
df -h

# 메모리 사용량
free -h

# 현재 시간 확인
date
```

---

## 인스턴스 비용 절감 - Scheduled Downtime

운영 시간 외 인스턴스 자동 중지:

```bash
# AWS CLI 설치 (선택사항)
sudo apt install -y awscli

# 스케줄 설정 (자세한 방법은 AWS 문서 참조)
# 또는 AWS Console에서 수동 중지/시작
```

---

## FAQ

### Q: EC2 인스턴스 보안은?

**A:** 다음과 같이 강화하세요:
- SSH 포트를 특정 IP만 허용
- 강력한 키 페어 사용
- 정기적으로 인스턴스 패치
- `.env` 파일 권한 제한

```bash
# .env 파일 권한 설정
chmod 600 .env
```

### Q: 인스턴스 중지 vs 종료 차이?

**중지 (Stop):**
- 인스턴스 상태 보존
- 재시작 가능
- EBS 스토리지 비용만 발생

**종료 (Terminate):**
- 인스턴스 삭제
- 복구 불가능
- 모든 데이터 삭제

### Q: EC2 인스턴스 업그레이드 가능?

**A:** 가능합니다 (다운타임 최소):
1. 스냅샷 생성
2. 더 큰 인스턴스 타입으로 마이그레이션
3. 탄력적 IP 재할당

### Q: 자동 백업 설정?

**A:** S3 사용 (월 $0.023/GB):
```bash
# 수동 백업
tar -czf trendbot_backup_$(date +%Y%m%d).tar.gz ~/trend-bot-kr/
```

---

## 참고 문서

- **OPERATIONS_GUIDE.md** — 일반 운영 가이드
- **BOT_SPEC.md** — 트렌드봇 명세서
- **AWS EC2 설명서** — https://docs.aws.amazon.com/ec2/
- **AWS 프리 티어** — https://aws.amazon.com/free/

