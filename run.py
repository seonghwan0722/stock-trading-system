"""
AI 주식 자동매매 시스템 실행 스크립트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 백엔드 앱 실행
from backend.app import app

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 AI 주식 자동매매 시스템 시작")
    print("=" * 60)
    print(f"📍 서버 주소: http://localhost:5000")
    print(f"📍 대시보드: http://localhost:5000/")
    print(f"📍 전략 설정: http://localhost:5000/strategy-config.html")
    print("=" * 60)
    print("")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
