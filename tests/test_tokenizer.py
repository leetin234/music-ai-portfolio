"""토크나이저 왕복 변환 테스트.

Phase 1 완료 기준(DoD): 합성 샘플 및 실제 ComMU 샘플에 대해
position/pitch/duration은 정확히, velocity는 양자화 오차 내에서 보존된다.

실행:
    pytest tests/ -v
    pytest tests/ -v -m commu     # 실제 데이터가 있을 때만
"""

import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import miditoolkit
from miditoolkit.midi import containers as ct

from data.parser import (
    GRID_PER_QUARTER,
    bar_grid_length,
    bucket_num_measures,
    normalize_instrument,
    parse_chord_progression,
    parse_midi,
    quantize_velocity,
    to_midi,
    verify_chord_grid,
)
from data.tokenizer import REMITokenizer, SampleMeta

CONFIG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "configs", "tokenizer.yaml")


@pytest.fixture(scope="module")
def tok():
    return REMITokenizer(CONFIG)


def _fingerprint(sample):
    """velocity는 양자화값으로 비교한다 (64단계 양자화는 비가역)."""
    return sorted((n.position, quantize_velocity(n.velocity), n.pitch, n.duration)
                  for n in sample.notes)


def _make_midi(path, num_bars=8, notes_per_bar=6, seed=0):
    random.seed(seed)
    tpb = 480
    tpg = tpb / GRID_PER_QUARTER
    midi = miditoolkit.MidiFile()
    midi.ticks_per_beat = tpb
    midi.time_signature_changes = [ct.TimeSignature(4, 4, 0)]
    inst = ct.Instrument(program=0)
    for bar in range(num_bars):
        for _ in range(notes_per_bar):
            pos = bar * 128 + random.choice([0, 16, 32, 48, 64, 80, 96, 112])
            inst.notes.append(ct.Note(
                velocity=random.randint(20, 120),
                pitch=random.randint(48, 84),
                start=int(pos * tpg),
                end=int((pos + random.choice([8, 16, 32, 64])) * tpg),
            ))
    midi.instruments = [inst]
    midi.dump(path)
    return path


# ── 단위 테스트 ───────────────────────────────────────────────
def test_bar_grid_length():
    assert bar_grid_length(4, 4) == 128
    assert bar_grid_length(3, 4) == 96
    assert bar_grid_length(6, 8) == 96


def test_normalize_instrument():
    assert normalize_instrument("string_violin-3") == "string_violin"
    assert normalize_instrument("acoustic_piano") == "acoustic_piano"
    assert normalize_instrument("synth_bass_wobble-2") == "synth_bass_wobble"


def test_bucket_num_measures():
    assert bucket_num_measures(4) == 4
    assert bucket_num_measures(5) == 4      # pickup
    assert bucket_num_measures(9) == 8
    assert bucket_num_measures(17) == 16
    with pytest.raises(ValueError):
        bucket_num_measures(12)


def test_chord_grid_is_eighth_note():
    """코드 격자가 8분음표 단위라는 가정."""
    assert verify_chord_grid(64, 4, 4, 8)     # 8마디 4/4
    assert verify_chord_grid(32, 4, 4, 4)
    assert verify_chord_grid(96, 3, 4, 16)    # 16마디 3/4
    assert not verify_chord_grid(50, 4, 4, 8)


def test_chord_dedupe():
    prog = [["Am"] * 8 + ["F"] * 8]
    events = parse_chord_progression(prog)
    assert len(events) == 2
    assert events[0].position == 0 and events[0].symbol == "Am"
    assert events[1].position == 8 * 16 and events[1].symbol == "F"


def test_vocab_ids_are_stable(tok):
    """PAD/EOS/BAR는 0/1/2에 고정되어야 한다 (모델 마스킹이 이에 의존)."""
    assert tok.pad_id == 0
    assert tok.eos_id == 1
    assert tok.token2id["BAR"] == 2
    assert tok.vocab_size == len(set(tok.id2token))   # 중복 없음


def test_chord_vocab_is_108(tok):
    """관측된 61종이 아니라 12 root x 9 quality = 108종을 만들어야 한다."""
    chords = [t for t in tok.id2token if t.startswith("Chord_")]
    assert len(chords) == 108


def test_instrument_category(tok):
    assert tok.instrument_category("accordion") == "keyboard"
    assert tok.instrument_category("string_violin-3") == "string"
    assert tok.instrument_category("orgel") == "idiophone"
    assert tok.instrument_category("timpani") == "percussion"
    assert tok.instrument_category("모르는악기") == "etc"    # fallback


# ── 왕복 테스트 ───────────────────────────────────────────────
@pytest.mark.parametrize("seed", range(5))
def test_roundtrip_synthetic(tok, tmp_path, seed):
    path = _make_midi(str(tmp_path / "s.mid"), seed=seed)
    sample = parse_midi(path, 4, 4, 8)
    sample.chords = parse_chord_progression([(["Am"] * 8 + ["F"] * 8) * 4])

    meta = SampleMeta(bpm=118, genre="cinematic", audio_key="aminor",
                      inst="string_violin-3", track_role="main_melody",
                      time_signature="4/4", pitch_range="mid_high",
                      num_measures=8, min_velocity=20, max_velocity=120,
                      sample_rhythm="standard")

    ids = tok.encode(sample, meta)
    _, restored = tok.decode(ids)

    assert _fingerprint(sample) == _fingerprint(restored)
    assert [(c.position, c.symbol) for c in sample.chords] == \
           [(c.position, c.symbol) for c in restored.chords]
    assert sample.num_bars == restored.num_bars


def test_roundtrip_through_midi(tok, tmp_path):
    """tokens -> ParsedSample -> MIDI -> ParsedSample 까지 보존되는가."""
    path = _make_midi(str(tmp_path / "s.mid"), seed=42)
    sample = parse_midi(path, 4, 4, 8)

    meta = SampleMeta(bpm=120, genre="newage", audio_key="cmajor",
                      inst="acoustic_piano", track_role="accompaniment",
                      time_signature="4/4", pitch_range="mid",
                      num_measures=8, min_velocity=20, max_velocity=120,
                      sample_rhythm="standard")

    _, restored = tok.decode(tok.encode(sample, meta))
    out = str(tmp_path / "out.mid")
    to_midi(restored, bpm=120).dump(out)
    again = parse_midi(out, 4, 4, 8)

    assert _fingerprint(sample) == _fingerprint(again)


def test_metadata_roundtrip(tok, tmp_path):
    path = _make_midi(str(tmp_path / "s.mid"))
    sample = parse_midi(path, 4, 4, 8)
    meta = SampleMeta(bpm=118, genre="cinematic", audio_key="aminor",
                      inst="string_violin-3", track_role="riff",
                      time_signature="4/4", pitch_range="high",
                      num_measures=9, min_velocity=101, max_velocity=127,
                      sample_rhythm="triplet")

    decoded, _ = tok.decode(tok.encode(sample, meta))
    assert decoded["Genre"] == "cinematic"
    assert decoded["Key"] == "aminor"
    assert decoded["Inst"] == "string"          # 카테고리로 축약됨
    assert decoded["Role"] == "riff"
    assert decoded["Rhythm"] == "triplet"
    assert decoded["NumMeasures"] == "8"        # 9 -> 버킷 8
    assert decoded["BPM"] == "120"              # 118 -> 5단위 양자화


# ── 실제 데이터 (있을 때만) ───────────────────────────────────
COMMU_META = "/content/drive/MyDrive/music-ai-portfolio/data/raw/commu_meta.csv"
COMMU_MIDI = "/content/drive/MyDrive/music-ai-portfolio/data/raw/commu_midi"


@pytest.mark.skipif(not os.path.exists(COMMU_META),
                    reason="ComMU 데이터셋이 없는 환경")
def test_roundtrip_real_samples():
    """실제 ComMU 샘플 200개에 대한 왕복 검증."""
    import pandas as pd
    from data.parser import parse_row

    tok = REMITokenizer(CONFIG)
    df = pd.read_csv(COMMU_META).sample(200, random_state=42)

    for _, row in df.iterrows():
        r = row.to_dict()
        sample = parse_row(r, COMMU_MIDI)
        meta = SampleMeta.from_row(r)
        _, restored = tok.decode(tok.encode(sample, meta))
        assert _fingerprint(sample) == _fingerprint(restored), r["id"]
