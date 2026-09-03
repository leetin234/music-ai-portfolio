"""학습 루프.

Phase 2 구현 대상.

필수 요소
---------
- gradient accumulation (유효 배치 256 맞추기)
- mixed precision (bf16 / fp16)
- **N step마다 Drive에 체크포인트 저장** ← Colab 세션 끊김 대비, 생략 금지
- 재개(resume) 로직
- W&B 로깅
"""


def train(config_path: str = "configs/base.yaml"):
    raise NotImplementedError


if __name__ == "__main__":
    train()
