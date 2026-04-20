#!/usr/bin/env python3
"""Wiki Linter — wiki 상태 검증 (Stop hook에서 자동 실행)
Usage: python3 scripts/wiki_lint.py
"""
import re
import json
from pathlib import Path
from datetime import date

BASE = Path(__file__).parent.parent
STUDY = BASE / "study"
ACTIVE = STUDY / "약점노트" / "active"


class WikiLinter:
    """llm-wiki Lint 패턴 — 4가지 건강 지표 검사"""

    def __init__(self):
        self.today = date.today().isoformat()
        self.issues: list[dict] = []

    def run(self) -> int:
        print(f"\n{'='*50}")
        print(f" WikiLinter — {self.today}")
        print(f"{'='*50}")
        self._check_orphan_links()
        self._check_sm2_overdue()
        self._check_index_completeness()
        self._check_study_weakness_mismatch()
        self._update_log()
        self._update_state()
        self._print_report()
        return len(self.issues)

    def _check_orphan_links(self):
        """[[파일명]] 링크 대상 파일 존재 확인"""
        all_files = {f.stem for f in STUDY.rglob("*.md")}
        for md in STUDY.rglob("*.md"):
            try:
                content = md.read_text(encoding="utf-8")
            except Exception:
                continue
            for raw in re.findall(r'\[\[([^\]]+)\]\]', content):
                # \| (markdown table escape) 와 | (alias) 모두 구분자로 처리
                link_part = re.split(r'\\?\|', raw)[0].strip()
                # path-style 링크 [[folder/file]] → stem만 추출
                link_name = Path(link_part).name if "/" in link_part else link_part
                if link_name not in all_files:
                    self.issues.append({
                        "type": "orphan_link",
                        "file": str(md.relative_to(BASE)),
                        "link": link_name,
                        "msg": f"[[{link_name}]] → 파일 없음  ({md.relative_to(BASE)})",
                    })

    def _check_sm2_overdue(self):
        """next_review <= 오늘인 약점노트 감지"""
        if not ACTIVE.exists():
            return
        for wf in ACTIVE.glob("w_*.md"):
            try:
                content = wf.read_text(encoding="utf-8")
            except Exception:
                continue
            m = re.search(r'next_review:\s*(\d{4}-\d{2}-\d{2})', content)
            if m and m.group(1) <= self.today:
                self.issues.append({
                    "type": "sm2_overdue",
                    "file": str(wf.relative_to(BASE)),
                    "next_review": m.group(1),
                    "msg": f"복습 대기: {wf.stem}  (due {m.group(1)})",
                })

    def _check_index_completeness(self):
        """study 개념 파일이 index.md에 없는 경우 감지"""
        index = STUDY / "index.md"
        if not index.exists():
            self.issues.append({"type": "missing_index", "msg": "study/index.md 없음"})
            return
        index_content = index.read_text(encoding="utf-8")
        projects_dir = STUDY / "projects"
        if not projects_dir.exists():
            return
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            for md in project_dir.glob("*.md"):
                if md.name == "README.md":
                    continue
                if f"[[{md.stem}]]" not in index_content:
                    self.issues.append({
                        "type": "index_missing",
                        "file": str(md.relative_to(BASE)),
                        "msg": f"index.md 누락: [[{md.stem}]]  ({md.relative_to(BASE)})",
                    })

    def _check_study_weakness_mismatch(self):
        """study 파일 있는데 w_*.md 없는 것 감지
        weakness 파일의 study_file: 필드로 명시적 역참조도 인식"""
        if not ACTIVE.exists():
            return
        # 직접 매칭: w_{stem}.md → {stem}
        weakness_stems = {f.stem[2:] for f in ACTIVE.glob("w_*.md")}
        # study_file: 역참조 매칭
        explicit_refs: set = set()
        for wf in ACTIVE.glob("w_*.md"):
            try:
                content = wf.read_text(encoding="utf-8")
            except Exception:
                continue
            m = re.search(r'^study_file:\s*(.+)', content, re.MULTILINE)
            if m:
                explicit_refs.add(m.group(1).strip().strip('"').strip("'"))
        covered = weakness_stems | explicit_refs
        projects_dir = STUDY / "projects"
        if not projects_dir.exists():
            return
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            for md in project_dir.glob("*.md"):
                if md.name == "README.md":
                    continue
                if md.stem not in covered:
                    self.issues.append({
                        "type": "no_weakness",
                        "file": str(md.relative_to(BASE)),
                        "msg": f"약점노트 없음: {md.stem}  (생성 조건 확인 필요)",
                    })

    def _update_log(self):
        log = STUDY / "log.md"
        summary = "이상 없음" if not self.issues else f"{len(self.issues)}개 문제"
        entry = f"## [{self.today}] lint | {summary}\n"
        if log.exists():
            with log.open("a", encoding="utf-8") as f:
                f.write(entry)

    def _update_state(self):
        state_path = STUDY / "state.json"
        if not state_path.exists():
            return
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["last_lint"] = self.today
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _print_report(self):
        if not self.issues:
            print(" ✅ 이상 없음\n")
            return
        by_type: dict[str, list] = {}
        for issue in self.issues:
            by_type.setdefault(issue["type"], []).append(issue["msg"])
        print(f" ⚠️  {len(self.issues)}개 문제 발견\n")
        for t, msgs in by_type.items():
            print(f"  [{t}] {len(msgs)}개")
            for msg in msgs:
                print(f"    • {msg}")
        print()


if __name__ == "__main__":
    exit(WikiLinter().run())
