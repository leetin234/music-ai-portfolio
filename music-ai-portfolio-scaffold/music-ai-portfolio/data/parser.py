"""MIDI 파일을 이벤트 시퀀스로 변환한다.

Phase 1 구현 대상.

이벤트 시퀀스 형태:
    [BAR, POSITION, CHORD, POSITION, VELOCITY, PITCH, DURATION, ...]

설계 원칙
---------
- tempo 토큰은 만들지 않는다 (BPM 메타데이터가 대체).
- position/duration 해상도는 128분음표 단위.
- 코드 진행은 position 토큰과 정렬해 시퀀스 안에 삽입한다.
"""

from typing import List, Dict, Any


def parse_midi(path: str) -> List[Dict[str, Any]]:
    """MIDI 파일 → 이벤트 딕셔너리 리스트.

    TODO(Phase 1):
        - miditoolkit으로 로드
        - tick을 128분음표 그리드로 양자화
        - 마디 경계 계산 (time_signature 반영)
        - 노트를 (position, velocity, pitch, duration)으로 변환
    """
    raise NotImplementedError


def events_to_midi(events: List[Dict[str, Any]], bpm: int = 120):
    """이벤트 시퀀스 → MIDI 객체. 왕복 변환 검증용.

    TODO(Phase 1): parse_midi의 정확한 역변환이어야 한다.
    """
    raise NotImplementedError
