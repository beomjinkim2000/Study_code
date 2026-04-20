#!/usr/bin/env python3
"""Wiki Validator — 페이지 콘텐츠 구조 검증 (harness execute.py 패턴)
wiki_lint.py: 링크·참조 관계 검사 (구조적 건강)
wiki_validate.py: 페이지 내용·형식 검증 (스키마 준수)

Usage: python3 scripts/wiki_validate.py [--project 과제5]
"""
import re
import json
import sys
import argparse
import contextlib
import itertools
import threading
import time
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))
import sm2

BASE = Path(__file__).resolve().parent.parent
STUDY = BASE / "study"
ACTIVE = STUDY / "약점노트" / "active"
SCHEMAS_DIR = Path(__file__).parent / "schemas"


# ── harness progress_indicator 패턴 ────────────────────────────────────────

@contextlib.contextmanager
def progress_indicator(label: str):
    """harness execute.py progress_indicator — 스피너 애니메이션"""
    frames = ["◐", "◓", "◑", "◒"]
    stop = threading.Event()

    def _spin():
        for f in itertools.cycle(frames):
            if stop.is_set():
                break
            print(f"\r  {f} {label}...", end="", flush=True)
            time.sleep(0.1)

    t = threading.Thread(target=_spin, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()
        t.join()
        print(f"\r  ✓ {label}          ")


# ── Schema Loader (harness _load_guardrails 패턴) ───────────────────────────

def _load_schema(name: str) -> dict:
    """schemas/{name}.json 로드 — harness _load_guardrails() 패턴"""
    path = SCHEMAS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """YAML frontmatter 파싱. 반환: (frontmatter_dict, body)"""
    if not content.startswith("---"):
        return {}, content
    end = content.find("\n---", 4)
    if end == -1:
        return {}, content
    fm_text = content[4:end]
    body = content[end + 4:].lstrip("\n")
    fm: dict = {}
    for line in fm_text.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            raw_v = v.strip().strip('"').strip("'")
            # 간단한 타입 변환 (JSON 파싱 불필요한 범위)
            if raw_v.lower() == "true":
                fm[k.strip()] = True
            elif raw_v.lower() == "false":
                fm[k.strip()] = False
            elif re.fullmatch(r"-?\d+", raw_v):
                fm[k.strip()] = int(raw_v)
            elif raw_v.startswith("[") and raw_v.endswith("]"):
                items = [i.strip().strip('"').strip("'") for i in raw_v[1:-1].split(",") if i.strip()]
                fm[k.strip()] = items
            else:
                fm[k.strip()] = raw_v
    return fm, body


# ── WikiValidator ────────────────────────────────────────────────────────────

class WikiValidator:
    """harness StepExecutor 패턴 — 스키마 기반 페이지 콘텐츠 검증

    wiki_lint.py가 wiki의 '연결 상태'를 검사한다면,
    wiki_validate.py는 '페이지 내용'이 스키마를 준수하는지 검사한다.
    """

    MAX_RETRIES = 3  # harness MAX_RETRIES 패턴 (미래 자동 수정 확장용)

    def __init__(self, project=None):
        self.project = project
        self.today = date.today().isoformat()
        self.errors = []
        self.warnings = []
        self._concept_schema = _load_schema("concept_page")
        self._weakness_schema = _load_schema("weakness_page")
        self._state_schema = _load_schema("state_schema")

    def run(self) -> int:
        print(f"\n{'='*50}")
        print(f" WikiValidator — {self.today}")
        if self.project:
            print(f" 프로젝트: {self.project}")
        print(f"{'='*50}")

        with progress_indicator("개념 페이지 검증"):
            self._validate_concept_pages()
        with progress_indicator("약점 페이지 검증"):
            self._validate_weakness_pages()
        with progress_indicator("state.json 검증"):
            self._validate_state_json()

        self._print_report()
        return len(self.errors)

    # ── 개념 페이지 검증 ──────────────────────────────────────────────────

    def _validate_concept_pages(self):
        projects_dir = STUDY / "projects"
        if not projects_dir.exists():
            return
        for project_dir in sorted(projects_dir.iterdir()):
            if not project_dir.is_dir():
                continue
            if self.project and project_dir.name != self.project:
                continue
            for md in sorted(project_dir.glob("*.md")):
                if md.name == "README.md":
                    continue
                self._check_concept_page(md)

    def _check_concept_page(self, path: Path):
        content = path.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(content)
        rel = str(path.relative_to(BASE))
        schema = self._concept_schema

        # 1. 필수 frontmatter 필드
        for field, rule in schema["required_frontmatter"].items():
            if field not in fm:
                self._add_error("missing_frontmatter", rel,
                                f"frontmatter에 '{field}' 없음  ({rel})")
            elif field == "type" and fm[field] not in rule.get("enum", []):
                self._add_error("invalid_frontmatter", rel,
                                f"type='{fm[field]}' 유효하지 않음. 허용: {rule['enum']}  ({rel})")
            elif field == "tags" and not isinstance(fm.get(field), list):
                self._add_error("invalid_frontmatter", rel,
                                f"tags는 배열이어야 함  ({rel})")

        # 2. 필수 섹션 (concept/synthesis 전용)
        page_type = fm.get("type", "concept")
        if page_type != "comparison":
            for sec_id, rule in schema["required_sections"].items():
                if not re.search(rule["pattern"], content, re.MULTILINE):
                    self._add_error("missing_section", rel,
                                    f"섹션 없음: '{rule['description']}'  ({rel})")

        # 3. comparison 타입 전용 규칙
        if page_type == "comparison":
            for _, rule in schema["required_sections_by_type"]["comparison"].items():
                if not re.search(rule["pattern"], content, re.MULTILINE):
                    self._add_error("missing_section", rel,
                                    f"비교 페이지에 비교표 없음  ({rel})")

        # 4. wikilinks 최소 개수
        min_links = schema["wikilinks"]["min_count"]
        links_found = re.findall(r'\[\[([^\]]+)\]\]', content)
        if len(links_found) < min_links:
            self._add_warning("few_wikilinks", rel,
                              f"[[링크]] {len(links_found)}개 (최소 {min_links}개 권장)  ({rel})")

    # ── 약점 페이지 검증 ──────────────────────────────────────────────────

    def _validate_weakness_pages(self):
        if not ACTIVE.exists():
            return
        for wf in sorted(ACTIVE.glob("w_*.md")):
            self._check_weakness_page(wf)

    def _check_weakness_page(self, path: Path):
        content = path.read_text(encoding="utf-8")
        fm, _ = _parse_frontmatter(content)
        rel = str(path.relative_to(BASE))
        schema = self._weakness_schema

        # 1. 필수 frontmatter 필드
        for field, rule in schema["required_frontmatter"].items():
            if field not in fm:
                self._add_error("missing_frontmatter", rel,
                                f"frontmatter에 '{field}' 없음  ({rel})")
                continue
            val = fm[field]
            if field == "level" and not (1 <= int(val) <= 4):
                self._add_error("invalid_frontmatter", rel,
                                f"level={val} 범위 초과 (1~4)  ({rel})")
            elif field == "next_review":
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(val)):
                    self._add_error("invalid_frontmatter", rel,
                                    f"next_review 형식 오류: '{val}' (YYYY-MM-DD 필요)  ({rel})")

        # 2. study 링크 존재 여부
        study_link_pattern = schema["required_sections"]["study_link"]["pattern"]
        if not re.search(study_link_pattern, content):
            self._add_error("missing_section", rel,
                            f"study 링크 없음 (> 상세: [[파일명]] 형식 필요)  ({rel})")

        # 3. 마스터 규칙 일관성 경고
        streak = fm.get("current_streak", 0)
        mastered = fm.get("mastered", False)
        if isinstance(streak, int) and streak >= 3 and not mastered:
            self._add_warning("mastery_inconsistent", rel,
                              f"current_streak={streak}이지만 mastered=false  ({rel})")

        # 4. SM-2 next_review 일관성 검증
        self._check_sm2_consistency(fm, rel)

    def _check_sm2_consistency(self, fm: dict, rel: str):
        """last_reviewed + history[-1] → 계산 next_review와 파일값 비교"""
        try:
            level = int(fm.get("level", 0))
            review_count = int(fm.get("review_count", 0))
            last_reviewed = fm.get("last_reviewed", "")
            stored_next = fm.get("next_review", "")
            history = fm.get("history", [])
        except (ValueError, TypeError):
            return

        if not last_reviewed or not stored_next:
            return
        if not history or not isinstance(history, list):
            return

        last_result = history[-1]
        try:
            from datetime import date as _date
            last_date = _date.fromisoformat(str(last_reviewed))
            expected = sm2.next_review_date(last_date, level, review_count - 1, last_result)
            expected_str = expected.isoformat()
        except Exception:
            return

        if expected_str != str(stored_next):
            self._add_warning("sm2_mismatch", rel,
                              f"SM-2 불일치: 파일={stored_next}, 계산={expected_str} "
                              f"(level={level}, last_result={last_result})  ({rel})")

    # ── state.json 검증 ───────────────────────────────────────────────────

    def _validate_state_json(self):
        state_path = STUDY / "state.json"
        if not state_path.exists():
            self._add_warning("missing_state", "study/state.json",
                              "study/state.json 없음 — bootstrap.py 실행 필요")
            return
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self._add_error("invalid_json", "study/state.json",
                            f"JSON 파싱 오류: {e}")
            return

        schema = self._state_schema
        for field in schema["required"]:
            if field not in state:
                self._add_error("missing_field", "study/state.json",
                                f"state.json에 '{field}' 없음")

        for proj_name, proj in state.get("projects", {}).items():
            proj_schema = schema["properties"]["projects"]["additionalProperties"]
            for field in proj_schema["required"]:
                if field not in proj:
                    self._add_error("missing_field", "study/state.json",
                                    f"projects.{proj_name}에 '{field}' 없음")
            status = proj.get("status")
            valid_statuses = proj_schema["properties"]["status"]["enum"]
            if status and status not in valid_statuses:
                self._add_error("invalid_field", "study/state.json",
                                f"projects.{proj_name}.status='{status}' 유효하지 않음")

    # ── 헬퍼 ─────────────────────────────────────────────────────────────

    def _add_error(self, err_type: str, file: str, msg: str):
        self.errors.append({"type": err_type, "file": file, "msg": msg})

    def _add_warning(self, warn_type: str, file: str, msg: str):
        self.warnings.append({"type": warn_type, "file": file, "msg": msg})

    def _print_report(self):
        total = len(self.errors) + len(self.warnings)
        print(f"\n{'='*50}")
        if not self.errors and not self.warnings:
            print(" ✅ 모든 페이지 스키마 준수\n")
            return

        if self.errors:
            print(f" ❌ 오류 {len(self.errors)}개\n")
            by_type: dict[str, list] = {}
            for e in self.errors:
                by_type.setdefault(e["type"], []).append(e["msg"])
            for t, msgs in by_type.items():
                print(f"  [{t}] {len(msgs)}개")
                for msg in msgs:
                    print(f"    • {msg}")

        if self.warnings:
            print(f"\n ⚠️  경고 {len(self.warnings)}개\n")
            for w in self.warnings:
                print(f"  [{w['type']}] {w['msg']}")

        print(f"\n 총 {total}개 항목\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wiki 페이지 스키마 검증")
    parser.add_argument("--project", help="특정 프로젝트만 검증 (예: 과제5)")
    args = parser.parse_args()
    sys.exit(WikiValidator(project=args.project).run())
