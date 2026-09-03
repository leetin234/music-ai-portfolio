"""Stage2 — 멀티트랙 조합기.

Phase 3 구현 대상. ⭐ **선행연구(ComMU)가 미해결로 남긴 부분.**
이 프로젝트의 가장 중요한 기여이므로 시간을 충분히 배분할 것.

조합 규칙은 3단계로 제한한다 (그 이상 복잡해지면 v2로 이월):
    1. 음역 충돌 해소 — track_role별 pitch range 규칙 적용
    2. 수직 화성 검사 — 동시 발음 노트가 코드톤/스케일에 속하는지
    3. velocity 밸런싱 — 멜로디 우선

면접 대비: "왜 단순히 이어붙이면 안 되는가"를
조합 전/후 불협화 비율 수치로 설명할 수 있어야 한다.
"""

# track_role별 권장 음역 (논문 Figure 4(b) 기반)
ROLE_PITCH_RANGE = {
    "main_melody":   ("mid_high", "high"),
    "sub_melody":    ("mid_high", "high"),
    "accompaniment": ("mid", "mid_high"),
    "bass":          ("very_low", "mid_low"),
    "pad":           ("mid", "mid_high"),
    "riff":          ("mid_high", "high"),
}


def combine_tracks(tracks, chord_progression, key):
    """TODO(Phase 3)"""
    raise NotImplementedError


def resolve_range_conflict(tracks):
    """TODO(Phase 3)"""
    raise NotImplementedError


def balance_velocity(tracks):
    """TODO(Phase 3)"""
    raise NotImplementedError
