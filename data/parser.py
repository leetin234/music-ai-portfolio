"""MIDI 파일과 메타데이터를 이벤트 표현으로 변환한다.

Phase 1 구현물.

해상도 정의
-----------
ComMU는 position/duration 해상도를 128분음표 단위로 쓴다.
즉 **온음표를 128등분**한 격자가 기본 단위이며, 4분음표 = 32 grid다.

    GRID_PER_WHOLE   = 128
    GRID_PER_QUARTER = 32
    ticks_per_grid   = ticks_per_beat / 32

마디 길이는 박자표에 따라 달라진다.

    4/4 -> 4 * (128/4) = 128 grid
    3/4 -> 3 * (128/4) =  96 grid
    6/8 -> 6 * (128/8) =  96 grid

코드 진행 격자
-------------
commu_meta.csv의 chord_progressions는 "코드 변화"가 아니라 **8분음표 격자**다.
num_measures별 평균 코드 수를 역산해 확인했다.

    4마디  -> 31.7 ~= 4 * 8   (4/4)
    8마디  -> 62.6 ~= 8 * 8   (4/4)
    16마디 -> 97.4 ~= 16 * 6  (3/4, 6/8이 다수)

따라서 격자 한 칸 = 8분음표 = 16 grid.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import miditoolkit

# ── 해상도 상수 ───────────────────────────────────────────────
GRID_PER_WHOLE = 128
GRID_PER_QUARTER = GRID_PER_WHOLE // 4      # 32
GRID_PER_EIGHTH = GRID_PER_WHOLE // 8       # 16 — 코드 격자 단위

MAX_DURATION = 128                          # duration 토큰 상한 (온음표)
INST_SUFFIX_RE = re.compile(r"-\d+$")


# ── 데이터 구조 ───────────────────────────────────────────────
@dataclass
class Note:
    """곡 시작을 0으로 하는 절대 grid 위치를 갖는 노트."""
    position: int
    velocity: int
    pitch: int
    duration: int


@dataclass
class ChordEvent:
    position: int
    symbol: str


@dataclass
class ParseStats:
    """손실이 발생한 지점을 기록한다. 무시하지 말고 집계해서 볼 것."""
    duration_clipped: int = 0       # MAX_DURATION 초과로 잘린 노트 수
    tick_residual: int = 0          # 격자에 정확히 안 떨어진 노트 수
    notes_out_of_range: int = 0     # num_measures 범위를 벗어난 노트 수


@dataclass
class ParsedSample:
    notes: List[Note]
    chords: List[ChordEvent]
    bar_grids: int                  # 한 마디의 grid 길이
    num_bars: int
    numerator: int
    denominator: int
    ticks_per_beat: int
    stats: ParseStats = field(default_factory=ParseStats)

    @property
    def total_grids(self) -> int:
        return self.bar_grids * self.num_bars


# ── 유틸 ──────────────────────────────────────────────────────
def bar_grid_length(numerator: int, denominator: int) -> int:
    """박자표 -> 한 마디의 grid 길이."""
    if GRID_PER_WHOLE % denominator != 0:
        raise ValueError(f"지원하지 않는 분모: {denominator}")
    return numerator * (GRID_PER_WHOLE // denominator)


def parse_time_signature(text: str) -> Tuple[int, int]:
    """'4/4' -> (4, 4)"""
    num, den = str(text).split("/")
    return int(num), int(den)


def normalize_instrument(inst: str) -> str:
    """'string_violin-3' -> 'string_violin'

    아티큘레이션 변형을 나타내는 '-숫자' 접미사를 제거한다.
    원본 130종이 38종으로 줄어든다.
    """
    return INST_SUFFIX_RE.sub("", inst)


def bucket_num_measures(n: int) -> int:
    """4/5 -> 4, 8/9 -> 8, 16/17 -> 16

    홀수 값은 pickup(못갖춘마디)이 붙은 경우다. 논문이 3종으로 처리했으므로
    같은 버킷으로 묶고, pickup 자체는 BAR 토큰 구조가 표현하게 둔다.
    """
    for bucket in (4, 8, 16):
        if n in (bucket, bucket + 1):
            return bucket
    raise ValueError(f"예상 밖의 num_measures: {n}")


def quantize_velocity(v: int, n_bins: int = 64) -> int:
    """velocity를 64단계로 양자화한다 (논문과 동일).

    ⚠️ 이 변환은 비가역이다. 왕복 테스트에서 velocity는
       양자화값끼리 비교해야 한다.
    """
    step = 128 // n_bins                      # 2
    return max(1, min(n_bins - 1, v // step))


def dequantize_velocity(b: int, n_bins: int = 64) -> int:
    step = 128 // n_bins
    return b * step


# ── 코드 진행 파싱 ────────────────────────────────────────────
def parse_chord_progression(raw: Any, dedupe: bool = True) -> List[ChordEvent]:
    """chord_progressions 컬럼 -> ChordEvent 리스트.

    Parameters
    ----------
    raw
        CSV에서 읽은 문자열 또는 이미 파싱된 리스트.
        구조는 이중 리스트이며 바깥 길이는 항상 1이다.
    dedupe
        True면 연속 중복 코드를 제거해 **변화 지점만** 남긴다.
        격자를 그대로 토큰화하면 시퀀스가 불필요하게 길어진다.
    """
    if isinstance(raw, str):
        raw = ast.literal_eval(raw)
    grid = raw[0] if (raw and isinstance(raw[0], list)) else raw

    events: List[ChordEvent] = []
    prev = None
    for i, symbol in enumerate(grid):
        if dedupe and symbol == prev:
            continue
        events.append(ChordEvent(position=i * GRID_PER_EIGHTH, symbol=symbol))
        prev = symbol
    return events


def verify_chord_grid(n_chords: int, numerator: int, denominator: int,
                      num_bars: int) -> bool:
    """코드 격자가 8분음표 단위라는 가정을 검증한다.

    한 마디의 8분음표 수 = numerator * (8 / denominator)
    """
    eighths_per_bar = numerator * 8 // denominator
    return n_chords == eighths_per_bar * num_bars


# ── MIDI 파싱 ─────────────────────────────────────────────────
def parse_midi(
    path: str,
    numerator: int | None = None,
    denominator: int | None = None,
    num_bars: int | None = None,
) -> ParsedSample:
    """MIDI 파일 -> ParsedSample.

    박자표와 마디 수는 메타데이터 CSV 값을 우선 사용한다.
    MIDI 헤더에도 있지만 CSV가 정본이다.
    """
    midi = miditoolkit.MidiFile(path)
    tpb = midi.ticks_per_beat

    if numerator is None or denominator is None:
        if midi.time_signature_changes:
            ts = midi.time_signature_changes[0]
            numerator, denominator = ts.numerator, ts.denominator
        else:
            numerator, denominator = 4, 4

    bar_grids = bar_grid_length(numerator, denominator)
    ticks_per_grid = tpb / GRID_PER_QUARTER

    stats = ParseStats()
    notes: List[Note] = []

    for inst in midi.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            pos_f = n.start / ticks_per_grid
            dur_f = (n.end - n.start) / ticks_per_grid

            pos = int(round(pos_f))
            dur = int(round(dur_f))

            if abs(pos_f - pos) > 1e-6 or abs(dur_f - dur) > 1e-6:
                stats.tick_residual += 1

            if dur > MAX_DURATION:
                dur = MAX_DURATION
                stats.duration_clipped += 1
            dur = max(1, dur)

            notes.append(Note(position=pos, velocity=n.velocity,
                              pitch=n.pitch, duration=dur))

    notes.sort(key=lambda x: (x.position, x.pitch))

    if num_bars is None:
        last = max((n.position for n in notes), default=0)
        num_bars = last // bar_grids + 1

    limit = bar_grids * num_bars
    stats.notes_out_of_range = sum(1 for n in notes if n.position >= limit)

    return ParsedSample(
        notes=notes,
        chords=[],
        bar_grids=bar_grids,
        num_bars=num_bars,
        numerator=numerator,
        denominator=denominator,
        ticks_per_beat=tpb,
        stats=stats,
    )


def parse_row(row: Dict[str, Any], midi_root: str) -> ParsedSample:
    """commu_meta.csv의 한 행 + 해당 MIDI -> ParsedSample.

    row는 pandas Series를 dict로 바꾼 것이어도 된다.
    """
    numerator, denominator = parse_time_signature(row["time_signature"])
    num_bars = int(row["num_measures"])
    path = os.path.join(midi_root, row["split_data"], "raw", f"{row['id']}.mid")

    sample = parse_midi(path, numerator, denominator, num_bars)
    sample.chords = parse_chord_progression(row["chord_progressions"])
    return sample


# ── 역변환 (왕복 검증용) ──────────────────────────────────────
def to_midi(sample: ParsedSample, bpm: int = 120,
            program: int = 0) -> miditoolkit.MidiFile:
    """ParsedSample -> MIDI. parse_midi의 역변환이어야 한다."""
    from miditoolkit.midi import containers as ct

    midi = miditoolkit.MidiFile()
    midi.ticks_per_beat = sample.ticks_per_beat
    ticks_per_grid = sample.ticks_per_beat / GRID_PER_QUARTER

    midi.tempo_changes = [ct.TempoChange(tempo=bpm, time=0)]
    midi.time_signature_changes = [
        ct.TimeSignature(numerator=sample.numerator,
                         denominator=sample.denominator, time=0)
    ]

    inst = ct.Instrument(program=program, is_drum=False)
    for n in sample.notes:
        start = int(round(n.position * ticks_per_grid))
        end = int(round((n.position + n.duration) * ticks_per_grid))
        inst.notes.append(
            ct.Note(velocity=n.velocity, pitch=n.pitch, start=start, end=end)
        )
    midi.instruments = [inst]
    return midi
