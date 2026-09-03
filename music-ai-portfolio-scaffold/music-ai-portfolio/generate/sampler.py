"""샘플링 및 코드 주입.

Phase 3 구현 대상.

논문 관측:
    temperature↑ → diversity↑ / controllability↓
    어휘가 작아 top_k 변화의 영향은 미미
"""


def sample(model, tokenizer, metadata, top_k=32, temperature=0.95):
    """TODO(Phase 3)"""
    raise NotImplementedError


def inject_chords(sequence, chord_progression):
    """추론 시 코드 토큰을 teacher forcing으로 삽입해 화성 진행을 강제한다.

    TODO(Phase 3)
    """
    raise NotImplementedError
