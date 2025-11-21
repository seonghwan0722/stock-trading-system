#!/usr/bin/env python3
"""
자동 커밋 및 푸시 스크립트
Claude Code와의 작업 후 변경사항을 자동으로 커밋하고 푸시합니다.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


class AutoCommit:
    def __init__(self, project_root: str = None):
        """
        Args:
            project_root: 프로젝트 루트 디렉토리 경로
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            # 스크립트 위치에서 상위 디렉토리로 이동
            self.project_root = Path(__file__).parent.parent

        self.changes = []
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def check_git_status(self) -> bool:
        """Git 상태 확인 및 변경사항 감지"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                self.changes = result.stdout.strip().split('\n')
                return True
            else:
                print("✅ 변경사항이 없습니다.")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Git 상태 확인 실패: {e}")
            return False

    def analyze_changes(self) -> dict:
        """변경사항 분석"""
        analysis = {
            'added': [],
            'modified': [],
            'deleted': [],
            'total': len(self.changes)
        }

        for change in self.changes:
            status = change[:2].strip()
            file_path = change[3:].strip()

            if status == 'A' or status == '??':
                analysis['added'].append(file_path)
            elif status == 'M':
                analysis['modified'].append(file_path)
            elif status == 'D':
                analysis['deleted'].append(file_path)

        return analysis

    def generate_commit_message(self, analysis: dict, custom_message: str = None) -> str:
        """커밋 메시지 자동 생성"""
        if custom_message:
            base_message = custom_message
        else:
            base_message = "chore: 자동 커밋"

        # 변경사항 요약
        summary = []
        if analysis['added']:
            summary.append(f"- 추가: {len(analysis['added'])}개 파일")
        if analysis['modified']:
            summary.append(f"- 수정: {len(analysis['modified'])}개 파일")
        if analysis['deleted']:
            summary.append(f"- 삭제: {len(analysis['deleted'])}개 파일")

        commit_msg = f"{base_message}\n\n"
        commit_msg += "\n".join(summary)
        commit_msg += f"\n\n타임스탬프: {self.timestamp}"
        commit_msg += "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"
        commit_msg += "\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

        return commit_msg

    def stage_files(self) -> bool:
        """변경된 파일 staging"""
        try:
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                check=True
            )
            print("✅ 파일 staging 완료")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Staging 실패: {e}")
            return False

    def commit(self, message: str) -> bool:
        """커밋 생성"""
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.project_root,
                check=True
            )
            print("✅ 커밋 생성 완료")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 커밋 실패: {e}")
            return False

    def push(self) -> bool:
        """원격 저장소에 푸시"""
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ GitHub에 푸시 완료")
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 푸시 실패: {e}")
            print(f"에러 메시지: {e.stderr}")
            return False

    def run(self, custom_message: str = None, auto_push: bool = True):
        """자동 커밋 실행"""
        print("=" * 60)
        print("🤖 자동 커밋 시스템")
        print("=" * 60)
        print()

        # 1. 변경사항 확인
        print("📋 변경사항 확인 중...")
        if not self.check_git_status():
            return

        # 2. 변경사항 분석
        analysis = self.analyze_changes()
        print(f"\n📊 변경사항 분석:")
        print(f"   - 추가된 파일: {len(analysis['added'])}개")
        print(f"   - 수정된 파일: {len(analysis['modified'])}개")
        print(f"   - 삭제된 파일: {len(analysis['deleted'])}개")
        print(f"   - 총 {analysis['total']}개 변경")
        print()

        # 3. 파일 staging
        if not self.stage_files():
            return

        # 4. 커밋 메시지 생성
        commit_msg = self.generate_commit_message(analysis, custom_message)
        print(f"\n💬 커밋 메시지:")
        print("-" * 60)
        print(commit_msg)
        print("-" * 60)
        print()

        # 5. 커밋 생성
        if not self.commit(commit_msg):
            return

        # 6. 푸시
        if auto_push:
            print(f"\n🚀 GitHub에 푸시 중...")
            self.push()

        print()
        print("=" * 60)
        print("✅ 자동 커밋 완료!")
        print("=" * 60)


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="자동 커밋 및 푸시 스크립트")
    parser.add_argument(
        "-m", "--message",
        type=str,
        help="커밋 메시지 (선택사항)",
        default=None
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="푸시하지 않고 커밋만 생성"
    )
    parser.add_argument(
        "-p", "--path",
        type=str,
        help="프로젝트 루트 경로 (기본값: 스크립트 상위 디렉토리)",
        default=None
    )

    args = parser.parse_args()

    auto_commit = AutoCommit(project_root=args.path)
    auto_commit.run(
        custom_message=args.message,
        auto_push=not args.no_push
    )


if __name__ == "__main__":
    main()
