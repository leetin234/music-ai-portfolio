"""트랙 순차 생성 오케스트레이션.

Phase 3 구현 대상.

흐름:
    1. track_role=main_melody로 멜로디 생성
    2. 멜로디에서 코드 진행 추출 (또는 사용자 지정 코드 사용)
    3. 코드를 고정한 채 track_role만 바꿔 순차 생성
       accompaniment → bass → pad → riff → sub_melody
"""

TRACK_ORDER = ["main_melody", "accompaniment", "bass", "pad", "riff", "sub_melody"]


def generate_song(model, tokenizer, metadata, roles=None):
    """TODO(Phase 3)"""
    raise NotImplementedError
