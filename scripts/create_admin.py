#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
관리자 계정 생성 스크립트
.env에 설정된 ADMIN_USERNAME과 ADMIN_PASSWORD로 초기 관리자 계정을 생성합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.mongo_db import get_user_manager
from backend.config import get_config

def create_admin_user():
    """관리자 계정 생성"""

    Config = get_config()

    # ADMIN_PASSWORD가 설정되어 있는지 확인
    if not Config.ADMIN_PASSWORD:
        print("❌ Error: ADMIN_PASSWORD가 .env 파일에 설정되어 있지 않습니다.")
        print("   .env 파일에 다음을 추가하세요:")
        print("   ADMIN_PASSWORD=your_secure_password")
        return False

    # 비밀번호 강도 확인
    if len(Config.ADMIN_PASSWORD) < 8:
        print("❌ Error: 비밀번호는 최소 8자 이상이어야 합니다.")
        return False

    user_manager = get_user_manager()

    # 이미 관리자 계정이 있는지 확인
    existing_admin = user_manager.users_collection.find_one({"username": Config.ADMIN_USERNAME})

    if existing_admin:
        print(f"⚠️  관리자 계정 '{Config.ADMIN_USERNAME}'이(가) 이미 존재합니다.")
        response = input("비밀번호를 업데이트하시겠습니까? (y/n): ")

        if response.lower() == 'y':
            # 비밀번호 업데이트
            result = user_manager.update_user(
                Config.ADMIN_USERNAME,
                {"password": Config.ADMIN_PASSWORD}
            )

            if result.get('success'):
                print(f"✅ 관리자 계정 '{Config.ADMIN_USERNAME}'의 비밀번호가 업데이트되었습니다.")
                return True
            else:
                print(f"❌ 비밀번호 업데이트 실패: {result.get('message')}")
                return False
        else:
            print("취소되었습니다.")
            return False

    # 새 관리자 계정 생성
    result = user_manager.create_user(
        username=Config.ADMIN_USERNAME,
        password=Config.ADMIN_PASSWORD,
        email=f"{Config.ADMIN_USERNAME}@localhost",
        full_name="Administrator",
        is_admin=True  # 관리자 권한 부여
    )

    if result.get('success'):
        print(f"✅ 관리자 계정 '{Config.ADMIN_USERNAME}'이(가) 성공적으로 생성되었습니다.")
        print(f"   사용자명: {Config.ADMIN_USERNAME}")
        print(f"   이메일: {Config.ADMIN_USERNAME}@localhost")
        print("\n⚠️  보안을 위해 .env 파일의 ADMIN_PASSWORD를 삭제하거나 주석 처리하세요.")
        return True
    else:
        print(f"❌ 관리자 계정 생성 실패: {result.get('message')}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("관리자 계정 생성")
    print("=" * 60)

    try:
        success = create_admin_user()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
