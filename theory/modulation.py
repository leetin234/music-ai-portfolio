"""전조 (modulation).

Phase 4 구현 대상. ⭐ 단순 이조가 아니라 **화성적으로 자연스러운 전조 경로**를
계산하는 것이 요점. 작곡 전공자만 설계할 수 있는 로직.

흐름:
    1. 원조와 목표조의 공통 화음(피벗 코드) 탐색
    2. 피벗 코드를 경유하는 연결부 코드 진행 제안
    3. 연결부 마디를 생성 모델로 채우기
"""


def find_pivot_chords(from_key: str, to_key: str):
    """두 조성의 공통 화음을 찾는다.

    TODO(Phase 4)
    """
    raise NotImplementedError


def build_modulation_path(from_key: str, to_key: str):
    """TODO(Phase 4)"""
    raise NotImplementedError
