"""MIDI → MusicXML 변환.

Phase 5 구현 대상.

주의: 박자표/조표가 깨지기 쉽다. music21로 quantize한 뒤 변환하고,
소절 단위 검증 스크립트를 함께 만들 것.
"""


def midi_to_musicxml(midi_path: str, out_path: str, key=None, time_sig=None):
    """TODO(Phase 5): 파트별 분리, 조표/박자표 반영"""
    raise NotImplementedError
