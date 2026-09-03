"""화성 및 조성 분석.

Phase 4 구현 대상.

music21의 기본 기능을 래핑하되, **기본 기능이 못 잡는 것을 직접 확장**하는 것이
차별화 포인트다. 래퍼만 만들면 "라이브러리 사용"에 그친다.

확장 대상:
    - 세컨더리 도미넌트 탐지
    - 논다이어토닉 / 차용 화음 표기
    - 텐션(9th, 11th, 13th) 식별
"""


def analyze_key(stream):
    """TODO(Phase 4): music21 key.analyze() 래핑"""
    raise NotImplementedError


def analyze_chords(stream):
    """TODO(Phase 4): chordify() 기반 + 기능화성 표기"""
    raise NotImplementedError


def detect_secondary_dominant(chords, key):
    """⭐ music21 기본 기능으로 안 되는 부분 — 직접 구현.

    TODO(Phase 4)
    """
    raise NotImplementedError
