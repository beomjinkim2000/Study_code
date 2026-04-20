#!/usr/bin/env python3
"""인사이트 로그 파일 저장 스크립트
Usage: python3 scripts/save_insight_log.py
  → stdin에서 마크다운 내용을 받아 YYYY-MM-DD_HH-MM.md 로 저장

파일명은 이 스크립트가 결정한다. Claude가 직접 파일명을 짓지 않는다.
"""
import sys
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent / "study" / "학습인사이트_log"


def save(content: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M") + ".md"
    path = LOG_DIR / filename
    if path.exists():
        # 같은 분에 두 번 실행되면 초 단위 suffix 추가
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".md"
        path = LOG_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"저장됨: study/학습인사이트_log/{filename}")
    return path


if __name__ == "__main__":
    content = sys.stdin.read()
    if not content.strip():
        print("[ERROR] 내용이 비어 있음. stdin으로 마크다운을 전달하라.", file=sys.stderr)
        sys.exit(1)
    save(content)
