"""이벤트 표현 <-> 정수 토큰 id 변환.

Phase 1 구현물. **이 프로젝트의 핵심 산출물 중 하나.**

시퀀스 구조
-----------
    [메타데이터 11종] [BAR] [Position][Chord] [Position][Velocity][Pitch][Duration] ... [EOS]

메타데이터 순서는 논문 Figure 8을 따른다.
노트 1개는 항상 4토큰(Position, Velocity, Pitch, Duration)이다.

REMI 원형 대비 차이
------------------
1. 메타데이터 11종을 시퀀스 앞에 prepend
2. 확장 화성(sus4/maj7/m7b5/min7) 포함 -> 코드 이벤트 108종
3. tempo 토큰 제거 (짧은 샘플에서 템포 변화가 없으므로 bpm이 대체)
4. 해상도를 32분음표 -> 128분음표로 상향

설계 메모
--------
- 코드 사전은 데이터에 관측된 61종이 아니라 12 root x 9 quality = 108종으로 만든다.
  원본 조성이 cmajor/aminor 2종뿐이라 관측값이 적을 뿐, key 증강 후 전부 등장한다.
- inst는 130종을 접미사 제거 -> 38종 -> 8 카테고리로 축약해 토큰화한다.
- lead 카테고리는 현재 비어 있으나 슬롯은 예약한다 (configs/tokenizer.yaml 참조).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import yaml

from .parser import (
    ChordEvent,
    Note,
    ParsedSample,
    bar_grid_length,
    bucket_num_measures,
    dequantize_velocity,
    normalize_instrument,
    parse_time_signature,
    quantize_velocity,
)

# 메타데이터 토큰 순서 (논문 Figure 8)
META_ORDER = [
    "bpm",
    "genre",
    "audio_key",
    "inst",
    "track_role",
    "time_signature",
    "pitch_range",
    "num_measures",
    "min_velocity",
    "max_velocity",
    "sample_rhythm",
]

UNK = "<unk>"

# audio_key 문자열 파싱: "c#minor" -> ("c#", "minor")
KEY_RE = re.compile(r"^([a-g]#?)(major|minor)$")


@dataclass
class SampleMeta:
    """토큰화에 필요한 메타데이터. CSV 한 행에서 뽑아온다."""
    bpm: int
    genre: str
    audio_key: str
    inst: str                # 원본 악기명 (내부에서 카테고리로 변환)
    track_role: str
    time_signature: str
    pitch_range: str
    num_measures: int
    min_velocity: int
    max_velocity: int
    sample_rhythm: str

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "SampleMeta":
        return cls(
            bpm=int(row["bpm"]),
            genre=str(row["genre"]),
            audio_key=str(row["audio_key"]),
            inst=str(row["inst"]),
            track_role=str(row["track_role"]),
            time_signature=str(row["time_signature"]),
            pitch_range=str(row["pitch_range"]),
            num_measures=int(row["num_measures"]),
            min_velocity=int(row["min_velocity"]),
            max_velocity=int(row["max_velocity"]),
            sample_rhythm=str(row["sample_rhythm"]),
        )


class REMITokenizer:
    """REMI 확장형 토크나이저."""

    def __init__(self, config_path: str = "configs/tokenizer.yaml"):
        with open(config_path, encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f)

        self.token2id: Dict[str, int] = {}
        self.id2token: List[str] = []

        # 악기명 -> 카테고리 역인덱스
        self.inst2cat: Dict[str, str] = {}
        for cat, items in self.cfg["instrument_map"].items():
            for name in (items or []):
                self.inst2cat[name] = cat

        self.build_vocab()

    # ── 사전 구축 ────────────────────────────────────────────
    def _add(self, token: str) -> None:
        if token not in self.token2id:
            self.token2id[token] = len(self.id2token)
            self.id2token.append(token)

    def build_vocab(self) -> None:
        cfg = self.cfg
        self.token2id.clear()
        self.id2token.clear()

        # 1) 특수 토큰 (id 0, 1, 2 고정)
        for name in ("PAD", "EOS", "BAR"):
            self._add(name)

        # 2) 메타데이터 — 각 필드의 첫 값은 unknown
        meta = cfg["metadata"]

        self._add("BPM_<unk>")
        lo, hi = meta["bpm"]["range"]
        step = meta["bpm"]["quantize_unit"]
        for v in range(lo, hi + 1, step):
            self._add(f"BPM_{v}")

        self._add("Genre_<unk>")
        for v in meta["genre"]["values"]:
            self._add(f"Genre_{v}")

        # audio_key: 원본은 2종이나 증강 후 24종이므로 전부 만든다
        self._add("Key_<unk>")
        for root in meta["audio_key"]["roots"]:
            for t in meta["audio_key"]["types"]:
                self._add(f"Key_{root}{t}")

        self._add("Inst_<unk>")
        for cat in cfg["instrument_map"].keys():
            self._add(f"Inst_{cat}")          # lead 포함 (현재 미사용, 슬롯 예약)

        self._add("Role_<unk>")
        for v in meta["track_role"]["values"]:
            self._add(f"Role_{v}")

        self._add("TimeSig_<unk>")
        for v in meta["time_signature"]["values"]:
            self._add(f"TimeSig_{v}")

        self._add("PitchRange_<unk>")
        for v in meta["pitch_range"]["values"]:
            self._add(f"PitchRange_{v}")

        self._add("NumMeasures_<unk>")
        for v in meta["num_measures"]["values"]:
            self._add(f"NumMeasures_{v}")

        self._add("MinVel_<unk>")
        self._add("MaxVel_<unk>")
        n_vel = cfg["note_tokens"]["velocity"]["size"]
        for b in range(n_vel):
            self._add(f"MinVel_{b}")
        for b in range(n_vel):
            self._add(f"MaxVel_{b}")

        self._add("Rhythm_<unk>")
        for v in meta["sample_rhythm"]["values"]:
            self._add(f"Rhythm_{v}")

        # 3) note sequence 토큰
        for p in range(cfg["note_tokens"]["position"]["size"]):
            self._add(f"Position_{p}")
        for b in range(n_vel):
            self._add(f"Velocity_{b}")
        for p in range(cfg["note_tokens"]["pitch"]["size"]):
            self._add(f"Pitch_{p}")
        for d in range(1, cfg["note_tokens"]["duration"]["size"] + 1):
            self._add(f"Duration_{d}")

        # 4) 코드 — 12 root x 9 quality = 108
        for root in cfg["note_tokens"]["chord"]["roots"]:
            for q in cfg["note_tokens"]["chord"]["qualities"]:
                self._add(f"Chord_{root}{q['symbol']}")

    @property
    def vocab_size(self) -> int:
        return len(self.id2token)

    @property
    def pad_id(self) -> int:
        return self.token2id["PAD"]

    @property
    def eos_id(self) -> int:
        return self.token2id["EOS"]

    # ── 헬퍼 ─────────────────────────────────────────────────
    def _id(self, token: str, fallback: str) -> int:
        """사전에 없으면 해당 필드의 unknown 토큰으로 대체한다."""
        return self.token2id.get(token, self.token2id[fallback])

    def _quantize_bpm(self, bpm: int) -> int:
        meta = self.cfg["metadata"]["bpm"]
        lo, hi = meta["range"]
        step = meta["quantize_unit"]
        v = int(round(bpm / step) * step)
        return max(lo, min(hi, v))

    def instrument_category(self, inst: str) -> str:
        return self.inst2cat.get(normalize_instrument(inst), "etc")

    # ── 인코딩 ───────────────────────────────────────────────
    def encode_metadata(self, m: SampleMeta) -> List[int]:
        n_vel = self.cfg["note_tokens"]["velocity"]["size"]
        cat = self.instrument_category(m.inst)
        return [
            self._id(f"BPM_{self._quantize_bpm(m.bpm)}", "BPM_<unk>"),
            self._id(f"Genre_{m.genre}", "Genre_<unk>"),
            self._id(f"Key_{m.audio_key}", "Key_<unk>"),
            self._id(f"Inst_{cat}", "Inst_<unk>"),
            self._id(f"Role_{m.track_role}", "Role_<unk>"),
            self._id(f"TimeSig_{m.time_signature}", "TimeSig_<unk>"),
            self._id(f"PitchRange_{m.pitch_range}", "PitchRange_<unk>"),
            self._id(f"NumMeasures_{bucket_num_measures(m.num_measures)}",
                     "NumMeasures_<unk>"),
            self._id(f"MinVel_{quantize_velocity(m.min_velocity, n_vel)}",
                     "MinVel_<unk>"),
            self._id(f"MaxVel_{quantize_velocity(m.max_velocity, n_vel)}",
                     "MaxVel_<unk>"),
            self._id(f"Rhythm_{m.sample_rhythm}", "Rhythm_<unk>"),
        ]

    def encode(self, sample: ParsedSample, meta: SampleMeta,
               add_eos: bool = True) -> List[int]:
        """ParsedSample + 메타데이터 -> 토큰 id 리스트."""
        n_vel = self.cfg["note_tokens"]["velocity"]["size"]
        ids = self.encode_metadata(meta)

        bar_grids = sample.bar_grids

        # 마디별로 이벤트를 모은다. 같은 위치면 코드가 노트보다 먼저.
        events: List[Tuple[int, int, Any]] = []
        for c in sample.chords:
            events.append((c.position, 0, c))
        for n in sample.notes:
            events.append((n.position, 1, n))
        events.sort(key=lambda e: (e[0], e[1],
                                   getattr(e[2], "pitch", -1)))

        cur_bar = -1
        for pos, kind, ev in events:
            bar = pos // bar_grids
            in_bar = pos % bar_grids

            while cur_bar < bar:
                ids.append(self.token2id["BAR"])
                cur_bar += 1

            ids.append(self.token2id[f"Position_{in_bar}"])
            if kind == 0:
                ids.append(self._id(f"Chord_{ev.symbol}", "Genre_<unk>"))
            else:
                vb = quantize_velocity(ev.velocity, n_vel)
                ids.append(self.token2id[f"Velocity_{vb}"])
                ids.append(self.token2id[f"Pitch_{ev.pitch}"])
                ids.append(self.token2id[f"Duration_{ev.duration}"])

        if add_eos:
            ids.append(self.eos_id)
        return ids

    # ── 디코딩 ───────────────────────────────────────────────
    def decode(self, ids: List[int]) -> Tuple[Dict[str, Any], ParsedSample]:
        """토큰 id 리스트 -> (메타데이터 dict, ParsedSample)."""
        toks = [self.id2token[i] for i in ids]

        meta: Dict[str, Any] = {}
        i = 0
        prefixes = ["BPM", "Genre", "Key", "Inst", "Role",
                    "TimeSig", "PitchRange", "NumMeasures",
                    "MinVel", "MaxVel", "Rhythm"]
        for key in prefixes:
            if i < len(toks) and toks[i].startswith(key + "_"):
                meta[key] = toks[i][len(key) + 1:]
                i += 1

        numerator, denominator = parse_time_signature(
            meta.get("TimeSig", "4/4"))
        bar_grids = bar_grid_length(numerator, denominator)

        notes: List[Note] = []
        chords: List[ChordEvent] = []
        bar = -1
        pos_in_bar = 0

        while i < len(toks):
            t = toks[i]
            if t == "BAR":
                bar += 1
                i += 1
            elif t.startswith("Position_"):
                pos_in_bar = int(t.split("_")[1])
                i += 1
            elif t.startswith("Chord_"):
                chords.append(ChordEvent(
                    position=max(bar, 0) * bar_grids + pos_in_bar,
                    symbol=t[len("Chord_"):]))
                i += 1
            elif t.startswith("Velocity_"):
                # Velocity, Pitch, Duration 3연속을 기대한다
                if i + 2 < len(toks) and toks[i + 1].startswith("Pitch_") \
                        and toks[i + 2].startswith("Duration_"):
                    notes.append(Note(
                        position=max(bar, 0) * bar_grids + pos_in_bar,
                        velocity=dequantize_velocity(int(t.split("_")[1])),
                        pitch=int(toks[i + 1].split("_")[1]),
                        duration=int(toks[i + 2].split("_")[1]),
                    ))
                    i += 3
                else:
                    i += 1          # 깨진 시퀀스는 건너뛴다
            elif t == "EOS":
                break
            else:
                i += 1

        num_bars = bar + 1 if bar >= 0 else 1
        sample = ParsedSample(
            notes=notes, chords=chords, bar_grids=bar_grids,
            num_bars=num_bars, numerator=numerator,
            denominator=denominator, ticks_per_beat=480,
        )
        return meta, sample
