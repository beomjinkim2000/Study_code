#!/usr/bin/env python3
"""TutorValidator 단위 테스트
Usage: python3 scripts/test_tutor.py
"""
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def _make_validator(tmpdir):
    import tutor_validate as tv
    tv.BASE = tmpdir
    tv.STUDY = tmpdir / "study"
    tv.ACTIVE = tmpdir / "study" / "약점노트" / "active"
    (tv.STUDY / "약점노트" / "active").mkdir(parents=True, exist_ok=True)
    return tv.TutorValidator()


class TestQueueValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_queue(self, content):
        (self.tmpdir / "study" / "session_queue.md").write_text(content, encoding="utf-8")

    def test_valid_queue_states_pass(self):
        """허용된 3가지 상태는 오류 없음"""
        self._write_queue(
            "# 큐\n"
            "- [ ] 과제5/transform (상태: 이해중)\n"
            "- [ ] 과제5/super_init (상태: 구현중)\n"
            "- [ ] 과제5/Autoencoder (상태: 검증중)\n"
        )
        v = _make_validator(self.tmpdir)
        v._validate_queue()
        self.assertEqual(len(v.errors), 0)

    def test_invalid_state_raises_error(self):
        """허용되지 않은 상태(예: 시작중)는 오류"""
        self._write_queue("- [ ] 과제5/transform (상태: 시작중)\n")
        v = _make_validator(self.tmpdir)
        v._validate_queue()
        errs = [e for e in v.errors if e["type"] == "invalid_queue_state"]
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0]["state"], "시작중")

    def test_completed_item_warns(self):
        """✅ 항목이 queue에 있으면 경고"""
        self._write_queue("- [x] 과제5/transform (상태: 검증중) ✅\n")
        v = _make_validator(self.tmpdir)
        v._validate_queue()
        warns = [w for w in v.warnings if w["type"] == "completed_in_queue"]
        self.assertEqual(len(warns), 1)

    def test_missing_state_field_warns(self):
        """상태 필드 없는 항목은 경고"""
        self._write_queue("- [ ] 과제5/transform\n")
        v = _make_validator(self.tmpdir)
        v._validate_queue()
        warns = [w for w in v.warnings if w["type"] == "missing_queue_state"]
        self.assertEqual(len(warns), 1)

    def test_missing_queue_file_warns(self):
        """session_queue.md 없으면 경고 (오류 아님)"""
        v = _make_validator(self.tmpdir)
        v._validate_queue()
        warns = [w for w in v.warnings if w["type"] == "missing_queue"]
        self.assertEqual(len(warns), 1)
        self.assertEqual(len(v.errors), 0)


class TestInsightValidation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study").mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_insight(self, content):
        (self.tmpdir / "study" / "학습인사이트.md").write_text(content, encoding="utf-8")

    def test_valid_insight_passes(self):
        """필수 3개 섹션 모두 있으면 통과"""
        self._write_insight(
            "# 학습 인사이트\n\n"
            "## 현재 수준\n내용\n\n"
            "## 잘 잡힌 개념\n내용\n\n"
            "## 다음 세션 포인트\n내용\n"
        )
        v = _make_validator(self.tmpdir)
        v._validate_insight()
        errs = [e for e in v.errors if e["type"] == "missing_insight_section"]
        self.assertEqual(len(errs), 0)

    def test_missing_section_errors(self):
        """필수 섹션 누락 시 오류"""
        self._write_insight("# 학습 인사이트\n\n## 현재 수준\n내용\n")
        v = _make_validator(self.tmpdir)
        v._validate_insight()
        errs = [e for e in v.errors if e["type"] == "missing_insight_section"]
        self.assertEqual(len(errs), 2)  # 잘 잡힌 개념, 다음 세션 포인트 누락

    def test_missing_insight_file_warns(self):
        """학습인사이트.md 없으면 경고 (오류 아님)"""
        v = _make_validator(self.tmpdir)
        v._validate_insight()
        warns = [w for w in v.warnings if w["type"] == "missing_insight"]
        self.assertEqual(len(warns), 1)
        self.assertEqual(len(v.errors), 0)


class TestSM2Consistency(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / "study" / "약점노트" / "active").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_weakness(self, name, content):
        path = self.tmpdir / "study" / "약점노트" / "active" / name
        path.write_text(content, encoding="utf-8")

    def test_consistent_sm2_passes(self):
        """SM-2 계산값과 파일값이 일치하면 통과"""
        # L3, review_count=1, history=["perfect"] → next_interval(3, 0, "perfect") = 5
        # last_reviewed=2026-04-13 → next_review=2026-04-18
        self._write_weakness("w_test.md",
            "---\n"
            "concept: test\n"
            "level: 3\n"
            "current_streak: 1\n"
            "last_reviewed: 2026-04-13\n"
            "next_review: 2026-04-18\n"
            "review_count: 1\n"
            "history: [perfect]\n"
            "mastered: false\n"
            "---\n"
        )
        v = _make_validator(self.tmpdir)
        v._validate_sm2_consistency()
        mismatches = [w for w in v.warnings if w["type"] == "sm2_mismatch"]
        self.assertEqual(len(mismatches), 0)

    def test_inconsistent_sm2_warns(self):
        """SM-2 계산값과 파일값이 불일치하면 경고"""
        # L3, review_count=1, last_result=perfect → expected 5일 → 2026-04-18
        # 하지만 파일에는 wrong date 기록됨
        self._write_weakness("w_test.md",
            "---\n"
            "concept: test\n"
            "level: 3\n"
            "current_streak: 1\n"
            "last_reviewed: 2026-04-13\n"
            "next_review: 2026-04-25\n"
            "review_count: 1\n"
            "history: [perfect]\n"
            "mastered: false\n"
            "---\n"
        )
        v = _make_validator(self.tmpdir)
        v._validate_sm2_consistency()
        mismatches = [w for w in v.warnings if w["type"] == "sm2_mismatch"]
        self.assertEqual(len(mismatches), 1)


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    sys.exit(0 if result.result.wasSuccessful() else 1)
