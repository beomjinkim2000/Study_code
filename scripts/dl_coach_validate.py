#!/usr/bin/env python3
"""DL 코치 실험 로그 검증기 — dl_research_coach.md 명세 기반
Usage: python3 scripts/dl_coach_validate.py [project_name]
"""
import re
import sys
from contextlib import contextmanager
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent.parent
STUDY = BASE / "study"

VALID_PHASES = {"①", "②", "③", "④"}
REQUIRED_COLUMNS = ["#", "단계", "변경 사항", "가설", "val_loss", "val_acc", "결론", "다음 가설"]

SPINNER = ["◐", "◓", "◑", "◒"]


@contextmanager
def progress_indicator(label):
    print(f"  {SPINNER[0]} {label}...", end=" ", flush=True)
    yield
    print("완료")


class DLCoachValidator:
    """experiments/log.md 형식 5가지 검증"""

    def __init__(self, project=None):
        self.today = date.today().isoformat()
        self.project = project
        self.errors = []
        self.warnings = []

    def run(self):
        print(f"\n{'='*50}")
        print(f" DLCoachValidator — {self.today}")
        print(f"{'='*50}")

        log_files = self._find_log_files()
        if not log_files:
            print("  ⚠️  experiments/log.md 파일 없음 (실험 아직 시작 전)\n")
            return 0

        for log_path in log_files:
            project_name = log_path.parent.parent.name
            print(f"\n  프로젝트: {project_name}")
            content = log_path.read_text(encoding="utf-8")

            with progress_indicator("현재 단계 필드 확인"):
                self._check_current_phase(content, log_path)
            with progress_indicator("테이블 컬럼 검증"):
                self._check_table_columns(content, log_path)
            with progress_indicator("Baseline 행 확인"):
                self._check_baseline_row(content, log_path)
            with progress_indicator("실험 번호 연속성 확인"):
                self._check_number_continuity(content, log_path)
            with progress_indicator("다음 가설 열 확인"):
                self._check_next_hypothesis(content, log_path)

        self._print_report()
        return len(self.errors)

    def _find_log_files(self):
        projects_dir = STUDY / "projects"
        if not projects_dir.exists():
            return []
        if self.project:
            paths = [projects_dir / self.project / "experiments" / "log.md"]
            return [p for p in paths if p.exists()]
        return list(projects_dir.glob("*/experiments/log.md"))

    # ── ① 현재 단계 필드 ────────────────────────────────────────────

    def _check_current_phase(self, content, log_path):
        # 넓은 패턴: 둥근 숫자 기호 전반 허용 (유효성은 아래서 판단)
        m = re.search(r'현재\s*단계\s*[:：]\s*(\S+)', content)
        if not m:
            self.errors.append({
                "type": "missing_phase",
                "file": str(log_path.relative_to(BASE)),
                "msg": f"{log_path.parent.parent.name}/log.md: '현재 단계: ①②③④' 필드 없음"
            })
        else:
            phase = m.group(1).strip()
            if phase not in VALID_PHASES:
                self.errors.append({
                    "type": "invalid_phase",
                    "file": str(log_path.relative_to(BASE)),
                    "phase": phase,
                    "msg": f"유효하지 않은 단계: {phase} (①②③④만 허용)"
                })

    # ── ② 테이블 컬럼 검증 ──────────────────────────────────────────

    def _check_table_columns(self, content, log_path):
        # 헤더 행 찾기 (| # | 단계 | ... 형태)
        header_line = None
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("|") and "#" in stripped and "단계" in stripped:
                header_line = stripped
                break

        if not header_line:
            self.errors.append({
                "type": "missing_table",
                "file": str(log_path.relative_to(BASE)),
                "msg": f"{log_path.parent.parent.name}/log.md: 실험 테이블 없음"
            })
            return

        for col in REQUIRED_COLUMNS:
            if col not in header_line:
                self.errors.append({
                    "type": "missing_column",
                    "file": str(log_path.relative_to(BASE)),
                    "column": col,
                    "msg": f"필수 컬럼 누락: '{col}'"
                })

    # ── ③ Baseline 행 확인 ──────────────────────────────────────────

    def _check_baseline_row(self, content, log_path):
        rows = _parse_table_rows(content)
        if not rows:
            return  # 테이블 없음은 ②에서 이미 처리

        # #=0 행 존재 여부
        has_baseline = any(row.get("#", "").strip() == "0" for row in rows)
        if not has_baseline:
            self.errors.append({
                "type": "missing_baseline",
                "file": str(log_path.relative_to(BASE)),
                "msg": f"{log_path.parent.parent.name}/log.md: Baseline 행(#=0) 없음"
            })

    # ── ④ 실험 번호 연속성 ──────────────────────────────────────────

    def _check_number_continuity(self, content, log_path):
        rows = _parse_table_rows(content)
        if not rows:
            return

        nums = []
        for row in rows:
            raw = row.get("#", "").strip()
            if raw.isdigit():
                nums.append(int(raw))

        if len(nums) < 2:
            return

        nums.sort()
        for i in range(1, len(nums)):
            if nums[i] != nums[i - 1] + 1:
                missing = list(range(nums[i - 1] + 1, nums[i]))
                self.warnings.append({
                    "type": "gap_in_numbers",
                    "file": str(log_path.relative_to(BASE)),
                    "missing": missing,
                    "msg": f"실험 번호 불연속: #{nums[i-1]} 다음 #{nums[i]} (빠진 번호: {missing})"
                })

    # ── ⑤ 다음 가설 열 ──────────────────────────────────────────────

    def _check_next_hypothesis(self, content, log_path):
        rows = _parse_table_rows(content)
        if not rows or len(rows) < 2:
            return

        # 마지막 행 제외하고 "다음 가설" 열이 비어있으면 경고
        for row in rows[:-1]:
            next_hyp = row.get("다음 가설", "").strip().strip("-").strip()
            if not next_hyp:
                num = row.get("#", "?")
                self.warnings.append({
                    "type": "empty_next_hypothesis",
                    "file": str(log_path.relative_to(BASE)),
                    "row": num,
                    "msg": f"#={num} 행의 '다음 가설' 열이 비어있음 (마지막 행 제외)"
                })

    # ── 리포트 ────────────────────────────────────────────────────────

    def _print_report(self):
        print(f"\n{'='*50}")
        if not self.errors and not self.warnings:
            print(" ✅ DL 코치 로그 이상 없음\n")
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


def _parse_table_rows(content):
    """마크다운 테이블 → list[dict{column: value}]"""
    lines = content.splitlines()
    header = None
    rows = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break
            continue

        cells = [c.strip() for c in stripped.strip("|").split("|")]

        if header is None:
            # 헤더 행
            if "#" in cells and "단계" in cells:
                header = cells
                in_table = True
            continue

        # 구분선 건너뜀
        if all(re.match(r'^[-:]+$', c) for c in cells if c):
            continue

        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))

    return rows


if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else None
    validator = DLCoachValidator(project=project)
    sys.exit(validator.run())
