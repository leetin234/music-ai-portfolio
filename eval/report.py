"""평가 리포트 생성.

Phase 6 구현 대상.

자체 확장 지표 (⭐ 차별화):
    - 트랙 간 음역 중첩률
    - 코드 진행 준수율 (마디별)
    - track_role별 note density / note length 분포가 학습 데이터와 일치하는지
      (논문 Figure 3의 분포와 대조)
"""


def build_report(model, tokenizer, val_metadata, out_path: str):
    raise NotImplementedError
