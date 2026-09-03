"""토크나이저 왕복 변환 테스트.

Phase 1의 완료 기준(DoD): 무작위 100개 샘플에 대해 왕복 변환 오차 0.

    midi → events → tokens → events → midi
    비교 항목: 노트 수, 피치, 시작/종료 시각, velocity
"""

import pytest


@pytest.mark.skip(reason="Phase 1에서 구현")
def test_roundtrip_preserves_notes():
    raise NotImplementedError


@pytest.mark.skip(reason="Phase 1에서 구현")
def test_vocab_size_within_expected_range():
    """목표 어휘 크기: 약 730 내외"""
    raise NotImplementedError
