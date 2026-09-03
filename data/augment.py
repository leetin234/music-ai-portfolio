"""데이터 증강 — key/bpm 변형.

Phase 1 구현 대상.

⚠️ 증강은 controllability를 올리지만 diversity를 낮추는 트레이드오프가 있다.
   Phase 6 ablation에서 유무를 비교한 뒤 최종 채택 여부를 정한다.
"""


def augment_key(events, semitones: int):
    """조성 이조. pitch와 chord root를 함께 옮겨야 한다.

    TODO(Phase 1): pitch만 옮기고 chord를 놓치는 버그가 흔하니 테스트 필수.
    """
    raise NotImplementedError


def augment_bpm(events, metadata, delta: int):
    """BPM 변경. duration도 함께 조정된다.

    TODO(Phase 1)
    """
    raise NotImplementedError
