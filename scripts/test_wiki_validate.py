#!/usr/bin/env python3
"""WikiValidator 테스트 — 페이지별 스키마 검증 (harness test_execute.py 패턴)
각 테스트는 독립적인 임시 디렉토리 사용
Usage: python3 scripts/test_wiki_validate.py
"""
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent))


def _make_validator(tmpdir: Path, project=None):
    import wiki_validate
    wiki_validate.BASE = tmpdir
    wiki_validate.STUDY = tmpdir / "study"
    wiki_validate.ACTIVE = tmpdir / "study" / "약점노트" / "active"
    wiki_validate.SCHEMAS_DIR = Path(__file__).parent / "schemas"
    return wiki_validate.WikiValidator(project=project)


def _make_dirs(tmpdir: Path, project: str = "테스트"):
    (tmpdir / "study" / "projects" / project).mkdir(parents=True)
    (tmpdir / "study" / "약점노트" / "active").mkdir(parents=True)


VALID_CONCEPT = """\
---
type: concept
project: 테스트
tags: [딥러닝, 테스트]
---

# 테스트 개념

## 한 줄 요약
> 테스트 요약

## 왜 필요한가
테스트용 개념 설명

[[연관개념1]] [[연관개념2]]
"""

VALID_WEAKNESS = """\
---
concept: "테스트 개념"
level: 2
current_streak: 0
last_reviewed: 2026-04-17
next_review: 2026-04-20
review_count: 1
history: []
mastered: false
---

# w_테스트

> 상세: [[테스트개념]]

## 틀렸던 이유
테스트
"""


class TestConceptPageValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        _make_dirs(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _concept_path(self, name: str = "개념.md") -> Path:
        return self.tmpdir / "study" / "projects" / "테스트" / name

    def test_valid_concept_page_passes(self):
        """유효한 개념 페이지는 오류 없음"""
        self._concept_path().write_text(VALID_CONCEPT, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_concept_pages()
        self.assertEqual(len(v.errors), 0)

    def test_missing_frontmatter_type(self):
        """frontmatter에 type 없으면 오류"""
        content = VALID_CONCEPT.replace("type: concept\n", "")
        self._concept_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_concept_pages()
        errors = [e for e in v.errors if e["type"] == "missing_frontmatter"]
        self.assertTrue(any("type" in e["msg"] for e in errors))

    def test_invalid_type_value(self):
        """type이 허용값 외의 값이면 오류"""
        content = VALID_CONCEPT.replace("type: concept", "type: unknown_type")
        self._concept_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_concept_pages()
        errors = [e for e in v.errors if e["type"] == "invalid_frontmatter"]
        self.assertEqual(len(errors), 1)

    def test_missing_summary_section(self):
        """'## 한 줄 요약' 섹션 없으면 오류"""
        content = VALID_CONCEPT.replace("## 한 줄 요약\n> 테스트 요약\n\n", "")
        self._concept_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_concept_pages()
        errors = [e for e in v.errors if e["type"] == "missing_section"]
        self.assertTrue(len(errors) >= 1)

    def test_few_wikilinks_warning(self):
        """[[링크]] 2개 미만이면 경고 (오류 아님)"""
        content = VALID_CONCEPT.replace("[[연관개념1]] [[연관개념2]]", "[[연관개념1]]")
        self._concept_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_concept_pages()
        self.assertEqual(len(v.errors), 0)
        warnings = [w for w in v.warnings if w["type"] == "few_wikilinks"]
        self.assertEqual(len(warnings), 1)

    def test_comparison_page_needs_table(self):
        """comparison 타입은 비교표 없으면 오류"""
        content = VALID_CONCEPT.replace("type: concept", "type: comparison")
        content = content.replace("## 한 줄 요약\n> 테스트 요약\n\n## 왜 필요한가\n테스트용 개념 설명\n\n", "")
        self._concept_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_concept_pages()
        errors = [e for e in v.errors if e["type"] == "missing_section"]
        self.assertTrue(len(errors) >= 1)

    def test_readme_skipped(self):
        """README.md는 검증 대상 아님"""
        readme = self.tmpdir / "study" / "projects" / "테스트" / "README.md"
        readme.write_text("# README (no frontmatter)", encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_concept_pages()
        self.assertEqual(len(v.errors), 0)

    def test_project_filter(self):
        """--project 필터 — 다른 프로젝트 파일은 무시"""
        other_dir = self.tmpdir / "study" / "projects" / "다른프로젝트"
        other_dir.mkdir(parents=True)
        (other_dir / "개념.md").write_text("no frontmatter", encoding="utf-8")
        v = _make_validator(self.tmpdir, project="테스트")
        v._validate_concept_pages()
        # 테스트 프로젝트에 파일 없으므로 오류 없음
        self.assertEqual(len(v.errors), 0)


class TestWeaknessPageValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        _make_dirs(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _weakness_path(self, name: str = "w_테스트.md") -> Path:
        return self.tmpdir / "study" / "약점노트" / "active" / name

    def test_valid_weakness_page_passes(self):
        """유효한 약점 페이지는 오류 없음"""
        self._weakness_path().write_text(VALID_WEAKNESS, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_weakness_pages()
        self.assertEqual(len(v.errors), 0)

    def test_missing_next_review(self):
        """next_review 없으면 오류"""
        content = VALID_WEAKNESS.replace("next_review: 2026-04-20\n", "")
        self._weakness_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_weakness_pages()
        errors = [e for e in v.errors if "next_review" in e["msg"]]
        self.assertTrue(len(errors) >= 1)

    def test_invalid_next_review_format(self):
        """next_review 형식이 잘못되면 오류"""
        content = VALID_WEAKNESS.replace("next_review: 2026-04-20", "next_review: 20260420")
        self._weakness_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_weakness_pages()
        errors = [e for e in v.errors if "next_review" in e["msg"]]
        self.assertTrue(len(errors) >= 1)

    def test_invalid_level_range(self):
        """level이 1~4 범위 밖이면 오류"""
        content = VALID_WEAKNESS.replace("level: 2", "level: 5")
        self._weakness_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_weakness_pages()
        errors = [e for e in v.errors if "level" in e["msg"]]
        self.assertTrue(len(errors) >= 1)

    def test_missing_study_link(self):
        """study 링크 없으면 오류"""
        content = VALID_WEAKNESS.replace("> 상세: [[테스트개념]]", "")
        self._weakness_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_weakness_pages()
        errors = [e for e in v.errors if e["type"] == "missing_section"]
        self.assertTrue(len(errors) >= 1)

    def test_mastery_inconsistency_warning(self):
        """current_streak >= 3인데 mastered=false면 경고"""
        content = VALID_WEAKNESS.replace("current_streak: 0", "current_streak: 3")
        self._weakness_path().write_text(content, encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_weakness_pages()
        warnings = [w for w in v.warnings if w["type"] == "mastery_inconsistent"]
        self.assertEqual(len(warnings), 1)


class TestStateJsonValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        _make_dirs(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_state(self, data: dict):
        path = self.tmpdir / "study" / "state.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_valid_state_passes(self):
        """유효한 state.json은 오류 없음"""
        self._write_state({
            "version": "1.0",
            "last_lint": None,
            "active_project": "테스트",
            "projects": {
                "테스트": {
                    "status": "in_progress",
                    "bootstrapped_at": "2026-04-18",
                    "concepts_completed": 0,
                    "concepts_total": 5,
                }
            }
        })
        v = _make_validator(self.tmpdir)
        v._validate_state_json()
        self.assertEqual(len(v.errors), 0)

    def test_missing_required_top_field(self):
        """최상위 필수 필드 누락 시 오류"""
        self._write_state({
            "version": "1.0",
            "active_project": None,
            "projects": {}
            # last_lint 누락
        })
        v = _make_validator(self.tmpdir)
        v._validate_state_json()
        errors = [e for e in v.errors if "last_lint" in e["msg"]]
        self.assertTrue(len(errors) >= 1)

    def test_invalid_project_status(self):
        """프로젝트 status가 허용값 외이면 오류"""
        self._write_state({
            "version": "1.0",
            "last_lint": None,
            "active_project": "테스트",
            "projects": {
                "테스트": {
                    "status": "unknown_status",
                    "bootstrapped_at": "2026-04-18",
                    "concepts_completed": 0,
                    "concepts_total": 0,
                }
            }
        })
        v = _make_validator(self.tmpdir)
        v._validate_state_json()
        errors = [e for e in v.errors if "status" in e["msg"]]
        self.assertTrue(len(errors) >= 1)

    def test_missing_state_file_is_warning(self):
        """state.json 없으면 오류가 아닌 경고"""
        v = _make_validator(self.tmpdir)
        v._validate_state_json()
        self.assertEqual(len(v.errors), 0)
        warnings = [w for w in v.warnings if w["type"] == "missing_state"]
        self.assertEqual(len(warnings), 1)

    def test_invalid_json_is_error(self):
        """state.json이 유효한 JSON이 아니면 오류"""
        path = self.tmpdir / "study" / "state.json"
        path.write_text("{invalid json", encoding="utf-8")
        v = _make_validator(self.tmpdir)
        v._validate_state_json()
        errors = [e for e in v.errors if e["type"] == "invalid_json"]
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    sys.exit(0 if result.result.wasSuccessful() else 1)
