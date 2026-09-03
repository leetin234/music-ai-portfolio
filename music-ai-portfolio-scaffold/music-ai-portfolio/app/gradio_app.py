"""Gradio 데모.

Phase 5 구현 대상.

UI 흐름:
    메타데이터 입력 → 생성 → 악보 이미지 + 오디오 플레이어 + MIDI 다운로드
    (Phase 7) "이 트랙 다시 편곡" 버튼 추가
"""

import gradio as gr


def build_ui():
    raise NotImplementedError


if __name__ == "__main__":
    build_ui().launch()
