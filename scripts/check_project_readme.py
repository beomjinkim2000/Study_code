#!/usr/bin/env python3
"""프로젝트 구현 가이드 README 검증
Usage: python3 scripts/check_project_readme.py [project_name]

검사 항목:
  1. 필수 섹션 존재 (구현 순서 / 막혔을 때 참조 매핑 / 개념 파일 현황)
  2. 개념 파일 현황 — ✅ 표시된 파일이 실제로 존재하는지
  3. [[링크]] 대상 파일이 study/projects/{name}/ 에 존재하는지
  4. 미완료 구현 항목 ( - [ ] ) 개수 보고
"""
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
STUDY = BASE / "study"

REQUIRED_SECTIONS = [
    (r"##\s+구현\s*순서", "구현 순서 섹션"),
    (r"##\s+막혔을\s*때", "막혔을 때 참조 매핑 섹션"),
    (r"##\s+개념\s*파일\s*현황", "개념 파일 현황 섹션"),
]


def progress(msg: str):
    print(f"  ◐ {msg}...", end=" ", flush=True)


def done():
    print("완료")


class ProjectReadmeChecker:
    def __init__(self, project=None):
        self.project = project
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def _add_error(self, kind: str, msg: str):
        self.errors.append({"type": kind, "msg": msg})

    def _add_warning(self, kind: str, msg: str):
        self.warnings.append({"type": kind, "msg": msg})

    def run(self) -> int:
        print(f"\n{'='*50}")
        print(f" ProjectReadmeChecker — {__import__('datetime').date.today()}")
        print(f"{'='*50}")

        project_dirs = []
        if self.project:
            d = STUDY / "projects" / self.project
            if d.exists():
                project_dirs = [d]
            else:
                print(f"[ERROR] study/projects/{self.project}/ 없음")
                return 1
        else:
            project_dirs = [d for d in (STUDY / "projects").iterdir() if d.is_dir()]

        for pdir in sorted(project_dirs):
            self._check_project(pdir)

        self._print_report()
        return 1 if self.errors else 0

    def _check_project(self, pdir: Path):
        name = pdir.name
        readme = pdir / "README.md"

        progress(f"{name}/README.md 섹션 확인")
        if not readme.exists():
            done()
            self._add_error("missing_readme", f"{name}: README.md 없음")
            return
        content = readme.read_text(encoding="utf-8")
        done()

        # 1. 필수 섹션
        progress("필수 섹션 확인")
        for pattern, label in REQUIRED_SECTIONS:
            if not re.search(pattern, content):
                self._add_error("missing_section",
                                f"{name}/README.md: '{label}' 없음")
        done()

        # 2. 미완료 항목
        progress("미완료 구현 항목 확인")
        todo_items = re.findall(r"- \[ \]", content)
        if todo_items:
            self._add_warning("pending_items",
                              f"{name}/README.md: 미완료 항목 {len(todo_items)}개 ( - [ ] )")
        done()

        # 3. 개념 파일 현황 ✅ vs 실제 파일
        progress("개념 파일 현황 정합성 확인")
        for line in content.splitlines():
            m = re.match(r"\|\s*(\S+\.md)\s*\|\s*✅", line)
            if m:
                fname = m.group(1)
                if not (pdir / fname).exists():
                    self._add_error("concept_file_missing",
                                    f"{name}/README.md: ✅ 표시됐지만 파일 없음 → {fname}")
        done()

        # 4. [[링크]] orphan 체크
        progress("[[링크]] 존재 확인")
        for link in re.findall(r"\[\[([^\]|]+)", content):
            target = pdir / f"{link}.md"
            if not target.exists():
                self._add_warning("orphan_link",
                                  f"{name}/README.md: [[{link}]] → 파일 없음")
        done()

    def _print_report(self):
        print(f"\n{'='*50}")
        if not self.errors and not self.warnings:
            print(" ✅ 프로젝트 README 이상 없음")
        else:
            if self.errors:
                print(f" ❌ 오류 {len(self.errors)}개")
                for e in self.errors:
                    print(f"  [ERROR] {e['msg']}")
            if self.warnings:
                print(f" ⚠️  경고 {len(self.warnings)}개")
                for w in self.warnings:
                    print(f"  [WARN]  {w['msg']}")


if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(ProjectReadmeChecker(project).run())
