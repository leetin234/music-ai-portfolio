"""Diversity 지표.

Phase 6 구현 대상.

동일 메타데이터로 n개를 생성한 뒤 pairwise distance의 평균을 구한다.
거리 = sqrt( ((1-chroma_sim)^2 + (1-groove_sim)^2) / 2 )

참고 수치 (논문 baseline, K=32/τ=0.95): D = 0.3160
"""


def chroma_similarity(a, b) -> float:
    """피치 클래스 분포의 코사인 유사도"""
    raise NotImplementedError


def groove_similarity(a, b) -> float:
    """리듬 패턴의 코사인 유사도"""
    raise NotImplementedError


def diversity(samples) -> float:
    raise NotImplementedError
