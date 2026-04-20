#!/usr/bin/env python3
"""SM-2 간격 반복 계산 모듈 — document_skill.md §4 명세 구현

이 모듈은 weakness 파일의 다음 복습일 계산 기준이 된다.
wiki_validate.py와 tutor_validate.py가 이 모듈을 import해서 일관성 검증에 사용.
"""
from datetime import date, timedelta

# 기본 간격표 (level → review_count 인덱스별 일수)
# review_count=0이면 첫 번째 값, 이후 누적될수록 인덱스 증가 (마지막 값 반복)
BASE_INTERVALS = {
    4: [1, 3, 7, 14, 30],    # L4 완전모름
    3: [2, 5, 12, 25, 50],   # L3 어려움
    2: [3, 7, 16, 35],       # L2 보통
    1: [5, 12, 28],          # L1 쉬움
}

# 정답 품질별 배율 (document_skill.md §4 "정답 품질 조정" 표)
MULTIPLIERS = {
    "perfect": 2.5,   # 힌트 없이 정답
    "hint1":   1.5,   # 힌트 1번 후 정답
    "hint2":   1.0,   # 힌트 2번 후 정답
    "hint3":   0.5,   # 힌트 3번 후 정답 (최소 1일 보장)
    "fail":    None,  # 끝까지 못맞춤 → 1일 리셋
}

VALID_LEVELS = set(BASE_INTERVALS.keys())
VALID_RESULTS = set(MULTIPLIERS.keys())


def next_interval(level: int, review_count: int, result: str) -> int:
    """다음 복습까지 일수 계산.

    Args:
        level: 난이도 레벨 (1~4)
        review_count: 이번 복습 전까지 누적 복습 횟수 (0-based)
        result: 복습 결과 (perfect|hint1|hint2|hint3|fail)

    Returns:
        다음 복습까지 일수 (최소 1일)
    """
    if level not in VALID_LEVELS:
        raise ValueError(f"유효하지 않은 레벨: {level} (1~4만 허용)")
    if result not in VALID_RESULTS:
        raise ValueError(f"유효하지 않은 결과: {result}")

    if result == "fail":
        return 1

    intervals = BASE_INTERVALS[level]
    idx = min(review_count, len(intervals) - 1)
    base = intervals[idx]
    days = round(base * MULTIPLIERS[result])
    return max(1, days)


def next_review_date(last_reviewed: date, level: int, review_count: int, result: str) -> date:
    """다음 복습 날짜 계산.

    Args:
        last_reviewed: 마지막 복습 날짜
        level: 난이도 레벨 (1~4)
        review_count: 이번 복습 전까지 누적 복습 횟수
        result: 복습 결과

    Returns:
        다음 복습 날짜 (date 객체)
    """
    days = next_interval(level, review_count, result)
    return last_reviewed + timedelta(days=days)


def is_mastered(current_streak: int) -> bool:
    """힌트 없이 3번 연속 정답(perfect) 여부 — document_skill.md §4 마스터 기준."""
    return current_streak >= 3


def update_streak(current_streak: int, result: str) -> int:
    """복습 결과에 따른 연속 정답 스트릭 업데이트."""
    if result == "perfect":
        return current_streak + 1
    return 0  # perfect 이외는 스트릭 리셋
