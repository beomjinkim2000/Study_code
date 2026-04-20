#!/usr/bin/env python3
"""튜터 워크플로우 검증기 — session_queue, 학습인사이트, SM-2 일관성
Usage: python3 scripts/tutor_validate.py
"""
import re
import sys
from contextlib import contextmanager
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sm2

BASE = Path(__file__).parent.parent
STUDY = BASE / "study"
ACTIVE = STUDY / "약점노트" / "active"

VALID_STATES = {"이해중", "구현중", "검증중"}
REQUIRED_INSIGHT_SECTIONS = ["## 현재 수준", "## 잘 잡힌 개념", "## 다음 세션 포인트"]

SPINNER = ["◐", "◓", "◑", "◒"]


@contextmanager
def progress_indicator(label):
    print(f"  {SPINNER[0]} {label}...", end=" ", flush=True)
    yield
    print("완료")


class TutorValidator:
    """튜터 워크플로우 3가지 검증: queue 형식, 인사이트 섹션, SM-2 일관성"""

    def __init__(self):
        self.today = date.today().isoformat()
        self.errors = []
        self.warnings = []

    def run(self):
        print(f"\n{'='*50}")
        print(f" TutorValidator — {self.today}")
        print(f"{'='*50}")

        with progress_indicator("session_queue.md 검증"):
            self._validate_queue()
        with progress_indicator("학습인사이트.md 검증"):
            self._validate_insight()
        with progress_indicator("SM-2 일관성 검증"):
            self._validate_sm2_consistency()

        self._print_report()
        return len(self.errors)

    # ── ① session_queue.md ──────────────────────────────────────────

    def _validate_queue(self):
        queue_path = STUDY / "session_queue.md"
        if not queue_path.exists():
            self.warnings.append({
                "type": "missing_queue",
                "msg": "session_queue.md 없음 (세션 시작 전 상태)"
            })
            return

        content = queue_path.read_text(encoding="utf-8")
        # - [ ] 또는 - [x] 로 시작하는 항목만 검사
        for lineno, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if not re.match(r'^- \[[ x]\]', stripped):
                continue

            # 완료(✅) 항목이 queue에 남아있으면 경고
            if "✅" in stripped:
                self.warnings.append({
                    "type": "completed_in_queue",
                    "line": lineno,
                    "msg": f"완료 항목이 큐에 남아있음 (line {lineno}): {stripped[:60]}"
                })

            # 상태 필드 파싱
            m = re.search(r'\(상태:\s*([^)]+)\)', stripped)
            if m:
                state = m.group(1).strip()
                if state not in VALID_STATES:
                    self.errors.append({
                        "type": "invalid_queue_state",
                        "line": lineno,
                        "state": state,
                        "msg": f"유효하지 않은 상태 '{state}' (line {lineno}) — 허용: {VALID_STATES}"
                    })
            else:
                # 상태 필드 없는 항목 — 경고
                self.warnings.append({
                    "type": "missing_queue_state",
                    "line": lineno,
                    "msg": f"상태 필드 없음 (line {lineno}): {stripped[:60]}"
                })

    # ── ② 학습인사이트.md ────────────────────────────────────────────

    def _validate_insight(self):
        insight_path = STUDY / "학습인사이트.md"
        if not insight_path.exists():
            self.warnings.append({
                "type": "missing_insight",
                "msg": "학습인사이트.md 없음 (아직 세션 종료 전)"
            })
            return

        content = insight_path.read_text(encoding="utf-8")
        for section in REQUIRED_INSIGHT_SECTIONS:
            if section not in content:
                self.errors.append({
                    "type": "missing_insight_section",
                    "section": section,
                    "msg": f"학습인사이트.md 필수 섹션 누락: {section}"
                })

    # ── ③ SM-2 일관성 ────────────────────────────────────────────────

    def _validate_sm2_consistency(self):
        if not ACTIVE.exists():
            return

        for wf in sorted(ACTIVE.glob("w_*.md")):
            content = wf.read_text(encoding="utf-8")
            fm = _parse_frontmatter(content)
            if not fm:
                continue

            try:
                level = int(fm.get("level", 0))
                review_count = int(fm.get("review_count", 0))
                current_streak = int(fm.get("current_streak", 0))
                last_reviewed = fm.get("last_reviewed", "")
                stored_next = fm.get("next_review", "")
                history = fm.get("history", [])
            except (ValueError, TypeError):
                continue

            if not last_reviewed or not stored_next:
                continue

            # history에서 마지막 결과 추론 (있으면)
            if history and isinstance(history, list) and len(history) > 0:
                last_result = history[-1]
            else:
                # history 없으면 검증 스킵 (초기 상태)
                continue

            try:
                from datetime import date as _date
                last_date = _date.fromisoformat(last_reviewed)
                expected = sm2.next_review_date(last_date, level, review_count - 1, last_result)
                expected_str = expected.isoformat()
            except Exception:
                continue

            if expected_str != stored_next:
                self.warnings.append({
                    "type": "sm2_mismatch",
                    "file": wf.name,
                    "stored": stored_next,
                    "expected": expected_str,
                    "msg": (
                        f"SM-2 불일치 {wf.name}: "
                        f"파일={stored_next}, 계산={expected_str} "
                        f"(level={level}, review_count={review_count}, last_result={last_result})"
                    )
                })

    # ── 리포트 ────────────────────────────────────────────────────────

    def _print_report(self):
        print(f"\n{'='*50}")
        if not self.errors and not self.warnings:
            print(" ✅ 튜터 워크플로우 이상 없음\n")
            return

        if self.errors:
            print(f" ❌ 오류 {len(self.errors)}개")
            for e in self.errors:
                print(f"  [ERROR] {e['msg']}")
        if self.warnings:
            print(f" ⚠️  경고 {len(self.warnings)}개")
            for w in self.warnings:
                print(f"  [WARN]  {w['msg']}")
        print()


def _parse_frontmatter(content):
    """YAML frontmatter 파싱 → dict. 없으면 None."""
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    fm_text = content[3:end].strip()
    result = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        # 간단한 타입 변환
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            result[key] = [v.strip().strip('"').strip("'")
                           for v in inner.split(",") if v.strip()]
        elif val.lower() == "true":
            result[key] = True
        elif val.lower() == "false":
            result[key] = False
        elif val.isdigit():
            result[key] = int(val)
        else:
            result[key] = val.strip('"').strip("'")
    return result


if __name__ == "__main__":
    sys.exit(TutorValidator().run())
