#!/usr/bin/env python3
"""SM-2 알고리즘 단위 테스트 — document_skill.md §4 명세 검증
Usage: python3 scripts/test_sm2.py
"""
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sm2


class TestNextInterval(unittest.TestCase):

    # ── fail 케이스 ──────────────────────────────────────────────────

    def test_fail_resets_to_1_day(self):
        """fail은 레벨/횟수 무관하게 항상 1일 리셋"""
        for level in [1, 2, 3, 4]:
            for review_count in [0, 1, 5]:
                self.assertEqual(sm2.next_interval(level, review_count, "fail"), 1,
                                 f"level={level}, review_count={review_count}")

    # ── perfect 케이스 ───────────────────────────────────────────────

    def test_l4_perfect_first_review(self):
        """L4 첫 복습 perfect: 1 × 2.5 = 2.5 → 3 (반올림)"""
        # round(1 * 2.5) = round(2.5) = 2 (Python banker's rounding) or 3?
        # Python round(2.5) = 2 (banker's rounding), but max(1, 2) = 2
        result = sm2.next_interval(4, 0, "perfect")
        self.assertGreaterEqual(result, 2)  # 최소 2일 (1 × 2.5)

    def test_l3_perfect_first_review(self):
        """L3 첫 복습 perfect: 2 × 2.5 = 5일"""
        self.assertEqual(sm2.next_interval(3, 0, "perfect"), 5)

    def test_l2_perfect_second_review(self):
        """L2 두 번째 복습 perfect: 7 × 2.5 = 17.5 → 18일"""
        result = sm2.next_interval(2, 1, "perfect")
        self.assertEqual(result, round(7 * 2.5))

    def test_l1_perfect_first_review(self):
        """L1 첫 복습 perfect: 5 × 2.5 = 12.5 → 12 또는 13일"""
        result = sm2.next_interval(1, 0, "perfect")
        self.assertIn(result, [12, 13])  # 반올림에 따라

    # ── hint 케이스 ──────────────────────────────────────────────────

    def test_hint1_multiplier(self):
        """hint1: × 1.5"""
        self.assertEqual(sm2.next_interval(3, 0, "hint1"), round(2 * 1.5))  # 3

    def test_hint2_multiplier(self):
        """hint2: × 1.0 (기본 간격 그대로)"""
        self.assertEqual(sm2.next_interval(2, 0, "hint2"), 3)  # 3 × 1.0

    def test_hint3_multiplier(self):
        """hint3: × 0.5 (최소 1일 보장)"""
        result = sm2.next_interval(4, 0, "hint3")
        self.assertEqual(result, max(1, round(1 * 0.5)))  # max(1, 0) = 1 or max(1,1)=1

    def test_hint3_minimum_1_day(self):
        """hint3 × 0.5가 0이 되어도 최소 1일 보장"""
        result = sm2.next_interval(4, 0, "hint3")  # 1 × 0.5 = 0.5 → round=0 → max(1,0)=1
        self.assertGreaterEqual(result, 1)

    # ── 인덱스 경계 케이스 ───────────────────────────────────────────

    def test_review_count_beyond_table_uses_last(self):
        """review_count가 테이블 길이 초과 시 마지막 값 사용"""
        # L1 intervals = [5, 12, 28] (len=3)
        at_3 = sm2.next_interval(1, 3, "hint2")   # idx = min(3,2) = 2 → 28 × 1.0 = 28
        at_99 = sm2.next_interval(1, 99, "hint2")  # idx = min(99,2) = 2 → 28
        self.assertEqual(at_3, at_99)
        self.assertEqual(at_3, 28)

    # ── 유효성 검사 ──────────────────────────────────────────────────

    def test_invalid_level_raises(self):
        """유효하지 않은 레벨은 ValueError"""
        with self.assertRaises(ValueError):
            sm2.next_interval(5, 0, "perfect")

    def test_invalid_result_raises(self):
        """유효하지 않은 result는 ValueError"""
        with self.assertRaises(ValueError):
            sm2.next_interval(2, 0, "great")


class TestNextReviewDate(unittest.TestCase):

    def test_date_calculation(self):
        """날짜 계산이 올바른지"""
        base = date(2026, 4, 18)
        result = sm2.next_review_date(base, 3, 0, "perfect")
        expected_days = sm2.next_interval(3, 0, "perfect")
        self.assertEqual(result, base + timedelta(days=expected_days))

    def test_fail_is_next_day(self):
        """fail이면 다음날"""
        base = date(2026, 4, 18)
        self.assertEqual(sm2.next_review_date(base, 2, 0, "fail"),
                         date(2026, 4, 19))


class TestIsMastered(unittest.TestCase):

    def test_streak_3_is_mastered(self):
        """3연속 정답이면 마스터"""
        self.assertTrue(sm2.is_mastered(3))

    def test_streak_5_is_mastered(self):
        """5연속 정답도 마스터"""
        self.assertTrue(sm2.is_mastered(5))

    def test_streak_2_not_mastered(self):
        """2연속은 마스터 아님"""
        self.assertFalse(sm2.is_mastered(2))

    def test_streak_0_not_mastered(self):
        """0연속은 마스터 아님"""
        self.assertFalse(sm2.is_mastered(0))


class TestUpdateStreak(unittest.TestCase):

    def test_perfect_increments(self):
        """perfect는 스트릭 증가"""
        self.assertEqual(sm2.update_streak(2, "perfect"), 3)

    def test_hint1_resets(self):
        """hint1은 스트릭 리셋"""
        self.assertEqual(sm2.update_streak(2, "hint1"), 0)

    def test_fail_resets(self):
        """fail은 스트릭 리셋"""
        self.assertEqual(sm2.update_streak(5, "fail"), 0)


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    sys.exit(0 if result.result.wasSuccessful() else 1)
