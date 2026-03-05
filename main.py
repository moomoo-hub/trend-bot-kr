"""
트렌드봇 메인 진입점

사용법:
  python main.py        - 2시간마다 반복 실행 (즉시 1회 시작)
  python main.py once   - 1회만 실행 (테스트용)
  python main.py help   - 도움말 표시
"""

import sys
import os
from pathlib import Path

# User site-packages 경로 추가 (nohup 환경에서 모듈을 찾을 수 있도록)
user_site = os.path.expanduser("~/.local/lib/python3.9/site-packages")
if user_site not in sys.path:
    sys.path.insert(0, user_site)

from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
root_dir = Path(__file__).parent
load_dotenv(root_dir / ".env")

# src 폴더를 Python 경로에 추가
sys.path.insert(0, str(root_dir / 'src'))


def check_api_key() -> None:
    """API 키 확인"""
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key == "여기에_API_키_입력":
        print("\n[오류] ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("  .env 파일에서 ANTHROPIC_API_KEY=sk-ant-... 형식으로 입력하세요.")
        print("  API 키 발급: https://console.anthropic.com\n")
        sys.exit(1)


def print_help() -> None:
    """사용법 출력"""
    print("""
트렌드봇 사용법:
  python main.py        - 2시간마다 반복 실행 (즉시 1회 시작)
  python main.py once   - 1회만 실행 (테스트용, 시간 체크함)
  python main.py test   - 테스트 메시지 1회 발송 (시간 체크 무시)
  python main.py help   - 도움말 표시
""")


def main() -> None:
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "run"

    check_api_key()

    if mode == "once":
        from scheduler import run_cycle
        run_cycle()

    elif mode == "test":
        from scheduler import run_cycle
        run_cycle(skip_time_check=True)

    elif mode in ("run", ""):
        from scheduler import start_scheduler
        start_scheduler()

    elif mode in ("help", "-h", "--help"):
        print_help()

    else:
        print(f"[오류] 알 수 없는 모드: '{mode}'")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
