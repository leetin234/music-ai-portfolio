"""Controllability 지표.

Phase 6 구현 대상. 논문 지표를 그대로 채택한다.

    CP (pitch control)   : 지정 pitch range를 만족하는 노트 비율
    CV (velocity control): min/max velocity 범위 내 노트 비율
    CH (harmony control) : 불협화가 아닌 노트 비율

참고 수치 (논문 baseline, K=32/τ=0.95):
    CP 0.8412 / CV 0.9102 / CH 0.9946
"""


def pitch_control(generated, metadata) -> float:
    raise NotImplementedError


def velocity_control(generated, metadata) -> float:
    raise NotImplementedError


def harmony_control(generated, metadata) -> float:
    raise NotImplementedError
