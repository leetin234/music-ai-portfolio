"""Transformer 구성 요소를 직접 구현한다.

Phase 2 구현 대상. **허깅페이스 사전 구현체를 쓰지 않는 것이 요점.**
"직접 설계했다"는 근거가 되는 파일이므로 라이브러리 호출로 대체하지 말 것.
"""

import torch.nn as nn


class MultiHeadAttention(nn.Module):
    """TODO(Phase 2): scaled dot-product attention + causal mask"""
    pass


class PositionalEncoding(nn.Module):
    """TODO(Phase 2): sinusoidal 또는 learned. 둘 다 실험해볼 것."""
    pass


class FeedForward(nn.Module):
    """TODO(Phase 2)"""
    pass


class DecoderBlock(nn.Module):
    """TODO(Phase 2): pre-norm 구조 권장 (학습 안정성)"""
    pass
