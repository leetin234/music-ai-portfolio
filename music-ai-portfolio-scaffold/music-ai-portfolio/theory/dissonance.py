"""불협화 검출.

Phase 3에서 먼저 만들고 Phase 6에서 평가 지표로 승격시킨다.
(Phase 3 조합기가 이 함수를 필요로 하므로 순서를 지킬 것)

판정 규칙 (논문 harmony control 지표와 동일):
    1. 노트가 해당 조성의 스케일에 속하면 → 협화
    2. 스케일 밖이면, 지속 시간 동안 코드톤과 일치하는지 확인
    3. 둘 다 아니면 → 불협화
"""


def is_dissonant(pitch: int, chord, key) -> bool:
    """TODO(Phase 3)"""
    raise NotImplementedError


def dissonance_ratio(tracks, chord_progression, key) -> float:
    """불협화로 판정된 노트의 비율. 낮을수록 좋다.

    TODO(Phase 3)
    """
    raise NotImplementedError
