"""Decoder-only Transformer.

Phase 2 구현 대상.

학습 목표:
    메타데이터 토큰 구간은 loss에서 제외하고,
    note sequence 구간부터 다음 토큰 예측 손실을 계산한다.
    (논문 식 (1): sum over t>=12 of log p(x_t | x_<t))
"""

import torch.nn as nn


class MusicTransformer(nn.Module):
    """TODO(Phase 2)

    구현 후 반드시 할 것:
        샘플 100개로 오버피팅 테스트 → loss가 0에 수렴하지 않으면
        마스킹이나 loss 계산에 버그가 있다는 뜻.
        이걸 전체 학습 후에 발견하면 며칠을 날린다.
    """
    pass
