# 조건부 멀티트랙 심볼릭 음악 생성 시스템 — 개발계획서

> **프로젝트 코드네임**: (미정 — 예: `HarmonyStack`, `TrackWeaver`, `ComposerCo`)
> **작성일**: 2026-09-03 · **버전**: v0.1 (draft)
> **목표 기간**: 약 8~10주 (스트레치 포함 12주)
> **작업 환경**: Google Colab Pro+ (A100/L4), Google Drive, GitHub, W&B, HuggingFace

---

## 0. 문서 사용법

- 이 문서는 **살아있는 문서**입니다. Phase가 끝날 때마다 해당 섹션의 `상태`와 `실측 결과`를 갱신합니다.
- 각 Phase는 `목표 / 작업 항목 / 산출물 / 완료 기준(DoD)` 4단 구조로 통일되어 있습니다.
- 체크박스(`- [ ]`)는 Notion으로 import 시 그대로 to-do 블록이 됩니다.
- 변경 이력은 문서 최하단 `변경 로그`에 한 줄씩 추가합니다.

---

## 1. 프로젝트 개요

### 1.1 한 줄 정의

> 사용자가 지정한 음악적 메타데이터(장르·조성·코드 진행·트랙 역할 등)를 조건으로 **멜로디를 먼저 생성하고, 그 위에 반주·베이스·패드 트랙을 순차적으로 쌓아 완성곡을 만드는** 심볼릭 음악 생성 시스템. 생성 결과는 화성 분석·전조/이조를 거쳐 **오선지 악보와 오디오로 출력**된다.

### 1.2 배경 및 문제의식

기준 선행연구: **ComMU: Dataset for Combinatorial Music Generation** (Pozalabs, NeurIPS 2022 D&B Track)

ComMU는 12종 메타데이터로 조건부 생성을 수행하는 심볼릭 음악 데이터셋/베이스라인이며, 다음 두 가지를 명시적 한계로 남겨두었다.

| 원 논문의 한계 | 본 프로젝트의 대응 |
|---|---|
| **Stage2(트랙 조합) 미구현** — 트랙별 note sequence 생성(Stage1)까지만 다루고, 여러 트랙을 완성곡으로 조합하는 단계는 "전문가가 수동으로 해야 함"으로 남겨둠 | Stage2를 **화성 충돌 방지 로직 기반으로 자동화**하여 파이프라인 완성 |
| **장르·리듬 편중** — genre는 new age / cinematic 2종뿐이며, time signature는 4/4, rhythm은 standard에 크게 쏠려 있음 | **K-indie 계열 무드·장르 메타데이터를 신규 정의**하고 소량 데이터를 직접 라벨링해 확장 |

여기에 더해, 기존 연구 대부분이 생성 결과를 MIDI/오디오로만 내놓는 반면, 본 프로젝트는 **연주 가능한 오선지 악보 출력**과 **화성 분석·전조 기능**을 갖춘 실사용 가능한 도구 형태를 지향한다.

### 1.3 차별화 포인트 (포트폴리오 핵심 어필 지점)

1. **직접 구현한 Transformer** — 사전 구현체를 가져다 쓰지 않고 PyTorch로 아키텍처를 작성
2. **음악 이론 기반 조건화 설계** — track-role, extended chord quality를 활용한 조건 토큰 설계
3. **Stage2 조합 로직** — 선행연구가 남긴 미해결 과제를 직접 해결
4. **화성학 기반 평가 지표** — 불협화음 비율, 코드-스케일 정합성 등을 직접 정의·측정
5. **악보 렌더링 파이프라인** — 생성 결과를 실제 악보로 출력 (비음악 전공 개발자가 구현하기 어려운 영역)
6. **도메인 확장** — 국내 인디음악 계열 메타데이터 신규 정의

> ⚠️ **정직한 스코프 표기 원칙**: 포트폴리오 문서/면접에서 아래를 명확히 구분해 서술한다.
> - "직접 설계·학습한 것": 토크나이저, Transformer 아키텍처, 조건화 방식, Stage2 로직, 평가 지표
> - "기존 자산을 활용한 것": ComMU 데이터셋, REMI 표현 방식(확장), music21, MuseScore, (선택) MusicGen

---

## 2. 시스템 아키텍처

### 2.1 전체 파이프라인

```
┌─────────────────────────────────────────────────────────────┐
│  [A] 사용자 입력 (Gradio UI)                                  │
│      장르 / 조성 / BPM / 박자 / 코드 진행 / 악기 / 마디 수      │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  [B] 조건 토큰 인코딩 (metadata → token ids)                  │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  [C] Track Generator (Decoder-only Transformer)              │
│      track_role=main_melody 로 1차 생성                       │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  [D] 코드 진행 추출 / 확정 (music21 + 자체 로직)               │
│      멜로디로부터 화성 추론 또는 사용자 지정 코드 사용           │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  [E] 순차 트랙 생성 (동일 모델, track_role만 교체)             │
│      accompaniment → bass → pad → riff → sub_melody          │
│      * 코드 진행을 조건으로 고정 → 화성적 정합성 확보           │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  [F] Stage2: 멀티트랙 조합기                                  │
│      음역 충돌 해소 / 불협화 검출 및 리샘플링 / 밸런스 조정      │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌───────────────────┬───────────────────┬─────────────────────┐
│ [G] 화성 분석 모듈  │ [H] 편곡 모듈      │ [I] 출력 모듈        │
│  · 코드/조성 분석   │  · 메타데이터 교체  │  · MIDI              │
│  · 이조 (transpose)│  · 스타일 재생성    │  · 오디오 (SoundFont)│
│  · 전조 (modulate) │  · (스트레치) VAE   │  · 오선지 (MusicXML) │
└───────────────────┴───────────────────┴─────────────────────┘
```

### 2.2 모듈 구성

| 모듈 | 역할 | 성격 | 기술 |
|---|---|---|---|
| `data/` | MIDI 파싱, 증강, 토큰화 | 엔지니어링 | miditoolkit, pretty_midi |
| `model/` | Transformer 아키텍처, 학습 루프 | **모델링(핵심)** | PyTorch |
| `generate/` | 샘플링, 순차 트랙 생성, Stage2 조합 | **모델링+로직(핵심)** | PyTorch, 자체 로직 |
| `theory/` | 코드 분석, 전조/이조, 불협화 검출 | **도메인 로직(차별화)** | music21 + 자체 확장 |
| `render/` | MusicXML/악보/오디오 렌더링 | 엔지니어링 | music21, MuseScore, FluidSynth |
| `eval/` | Controllability / Diversity / Fidelity 측정 | **평가 설계(차별화)** | numpy, music21 |
| `app/` | Gradio 데모 UI | 엔지니어링 | Gradio, Verovio |

### 2.3 디렉토리 구조

```
music-ai-portfolio/
├── README.md                    # 프로젝트 소개 (포트폴리오 표지 역할)
├── requirements.txt
├── configs/
│   ├── base.yaml                # 모델/학습 하이퍼파라미터
│   └── tokenizer.yaml           # 토큰 사전 정의
├── data/
│   ├── raw/                     # ComMU 원본 + 자체 수집 MIDI
│   ├── processed/               # 토큰화된 npz/pt
│   ├── parser.py                # MIDI → 이벤트 시퀀스
│   ├── tokenizer.py             # 이벤트 → 정수 id (핵심 구현물)
│   └── augment.py               # key/bpm 증강
├── model/
│   ├── transformer.py           # Decoder-only Transformer (직접 구현)
│   ├── layers.py                # MHA, FFN, positional encoding
│   └── train.py                 # 학습 루프 + W&B 로깅
├── generate/
│   ├── sampler.py               # top-k / nucleus 샘플링
│   ├── sequential.py            # 트랙 순차 생성 오케스트레이션
│   └── combiner.py              # Stage2 조합 로직 (차별화 포인트)
├── theory/
│   ├── analysis.py              # 코드/조성 분석
│   ├── transpose.py             # 이조
│   ├── modulation.py            # 전조 (피벗 코드 탐색)
│   └── dissonance.py            # 불협화 검출
├── render/
│   ├── to_musicxml.py
│   ├── to_score.py              # MuseScore CLI 호출
│   └── to_audio.py              # SoundFont 렌더링
├── eval/
│   ├── controllability.py
│   ├── diversity.py
│   └── report.py
├── app/
│   └── gradio_app.py
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_tokenizer_test.ipynb
│   ├── 03_train.ipynb           # Colab 학습용 메인 노트북
│   └── 04_eval_report.ipynb
└── docs/
    ├── architecture.md
    ├── experiment_log.md        # 실험 일지 (Notion과 동기화)
    └── samples/                 # 생성 샘플 (MIDI/mp3/PNG)
```

---

## 3. 기술 스택

### 3.1 확정 스택

| 영역 | 도구 | 선정 이유 |
|---|---|---|
| 딥러닝 | **PyTorch** | 아키텍처를 raw하게 구현해야 "직접 설계" 근거가 됨 |
| MIDI 파싱 | **miditoolkit**, pretty_midi | REMI 계열 표현 구현 시 표준적으로 사용됨 |
| 음악 이론 | **music21** | 조성 분석, 화성 분석, 이조 기능 내장 + 확장 용이 |
| 악보 렌더링 | **MuseScore 4 (CLI)** | MusicXML → PNG/PDF, Colab에 설치 가능 |
| 웹 악보 표시 | **Verovio** (선택) | 브라우저에서 MusicXML → SVG 실시간 렌더 |
| 오디오 렌더링 | **FluidSynth + SoundFont** | MIDI → wav, 무료 SF2 사용 |
| 실험 관리 | **Weights & Biases** | loss curve / 하이퍼파라미터 비교, 포트폴리오 시각자료 |
| 데모 | **Gradio** + HuggingFace Spaces | 배포 간편, 링크 하나로 공유 가능 |
| 학습 환경 | **Colab Pro+ (A100 40GB)** | 백그라운드 실행, 장시간 학습 |
| 저장 | Google Drive (체크포인트), HF Hub (최종 모델) | Colab 세션 초기화 대비 |
| 문서 | GitHub + Notion | 코드/실험일지 이원 관리 |

### 3.2 스트레치(선택) 스택

- **audiocraft (MusicGen)** — 생성된 MIDI를 melody-conditioning 입력으로 넣어 오디오 품질 향상
- **Transformer-VAE 계열** — latent 보간 기반 스타일 트랜스퍼(편곡 고도화)

---

## 4. 데이터 설계

### 4.1 데이터 소스

| 소스 | 규모 | 용도 | 확보 방법 |
|---|---|---|---|
| **ComMU** | 11,144 샘플 / 526,612 노트 | 메인 학습 데이터 | 공개 릴리스 |
| Lakh MIDI (선택) | 대규모 | 사전학습 보강 | 공개 |
| **자체 K-indie 서브셋** | 목표 100~300 샘플 | 도메인 확장 (차별화) | 직접 채보/편집 + 메타데이터 라벨링 |

### 4.2 메타데이터 스키마

ComMU의 12종을 기반으로 하되, **본 프로젝트에서 확장하는 항목을 별도 표기**한다.

| # | 항목 | 값 예시 | 비고 |
|---|---|---|---|
| 1 | bpm | 35~160 (5단위 양자화) | |
| 2 | genre | new_age, cinematic **+ (확장) k_indie_lofi, k_indie_band, synth_pop** | 🔵 확장 |
| 3 | key | 12 root × 2 type = 24 | |
| 4 | instrument | 8 카테고리 (keyboard, lead, idiophone, plucked_string, string, wind, percussion, etc.) | |
| 5 | **track_role** | main_melody, sub_melody, accompaniment, bass, pad, riff | ⭐ 핵심 조건 |
| 6 | time_signature | 4/4, 3/4, 6/8 **+ (확장 검토) 5/4, 7/8** | 🔵 확장 |
| 7 | pitch_range | very_low ~ very_high (7단계) | |
| 8 | num_measures | 4, 8, 16 | |
| 9 | **chord_progression** | 시퀀스 형태 (position 토큰과 함께 인코딩) | ⭐ 핵심 조건 |
| 10 | min_velocity | 2~127 | |
| 11 | max_velocity | 2~127 | |
| 12 | rhythm | standard, triplet **+ (확장 검토) swing** | 🔵 확장 |

### 4.3 토큰 표현 (REMI 확장형)

```
[메타데이터 토큰 11종] + [BAR, POSITION, CHORD, PITCH, DURATION, VELOCITY, ... , EOS]
```

- **해상도**: 128분음표 단위 (선행연구 주관평가에서 humanness/richness 최고점)
- **코드 품질**: major, minor, dim, aug, dominant + **sus4, maj7, m7b5, min7** (확장 화성)
- **tempo 토큰 제외**: 짧은 샘플에서 템포 변화가 없으므로 BPM 메타데이터로 대체
- 어휘 크기 목표: 약 730 토큰 내외

### 4.4 데이터 증강

- key 증강: 12개 root 전조
- bpm 증강: -10, -5, 0, +5, +10
- 조합 시 원본 1개당 최대 60배 확장
- ⚠️ 증강은 controllability를 올리지만 **diversity를 떨어뜨리는 트레이드오프**가 있으므로, ablation으로 검증 후 채택 여부 결정

---

## 5. 모델 설계

### 5.1 아키텍처

- **Decoder-only Transformer** (auto-regressive language model)
- 학습 목표: 메타데이터 토큰 이후 note sequence 토큰에 대한 log-likelihood 최대화
  - 즉, 메타데이터 구간은 loss에서 제외하고 note 구간부터 예측

### 5.2 하이퍼파라미터 (초기값)

선행연구 baseline(13.7M 파라미터, 4×RTX3090)을 Colab 단일 GPU 환경에 맞게 조정.

| 항목 | 선행연구 | **본 프로젝트 초기값** | 비고 |
|---|---|---|---|
| layers | 6 | 6 | 동일 |
| heads | 10 | 8 | d_model 나눗셈 편의 |
| d_model | — | 512 | |
| d_ff | — | 2048 | |
| dropout | 0.1 | 0.1 | |
| batch size | 256 (4 GPU) | 32 × grad_accum 8 = 256 | 유효 배치 동일화 |
| optimizer | Adam | AdamW | |
| lr | 0.004 | 0.001 (재탐색 필요) | 단일 GPU 기준 재조정 |
| scheduler | inv_sqrt | inv_sqrt + warmup 100 | |
| precision | — | bf16 (mixed) | A100 활용 |
| max_seq_len | — | 1024 | 16마디 커버 확인 필요 |

> 📌 **학습 시간 추정**: 유효배치 256 기준, A100 1장에서 ComMU 전체 데이터 1 epoch ≈ 수 분 단위 예상.
> 선행연구는 6,000 epoch에서 최저 validation loss를 기록했으나, 본 프로젝트는 **early stopping 기반**으로 운영하고 실측치를 이 표에 갱신한다.

### 5.3 생성(Inference) 전략

- **샘플링**: top-k (K=32) + temperature (τ=0.95) 기본값
  - 선행연구 결과상 τ↑ → diversity↑ / controllability↓ 트레이드오프
  - 어휘 크기가 작아 K 변화의 영향은 미미
- **코드 주입(chord infusion)**: 추론 시 코드 토큰을 teacher forcing으로 삽입하여 화성 진행을 강제

---

## 6. Phase별 실행 계획

### Phase 0 — 환경 세팅 및 데이터 확보 (1주)

**목표**: 학습을 시작할 수 있는 상태 만들기

- [ ] GitHub 레포 생성, 디렉토리 구조 스캐폴딩
- [ ] Colab Pro+ 구독, A100 할당 확인, Drive 마운트 스크립트 작성
- [ ] ComMU 데이터셋 다운로드 및 라이선스 조건 확인
- [ ] 샘플 MIDI 10개를 열어 구조 육안 확인 (`notebooks/01_data_exploration.ipynb`)
- [ ] W&B 프로젝트 생성 및 연동 테스트
- [ ] requirements.txt 고정 (버전 pin — Colab 환경 변경 대비)

**산출물**: 레포 스캐폴드, 데이터 EDA 노트북
**DoD**: Colab에서 `import` 전부 성공 + 데이터 로드 성공

---

### Phase 1 — 데이터 파이프라인 & 토크나이저 (1.5주)

**목표**: MIDI ↔ 토큰 시퀀스 무손실 왕복 변환

- [ ] `parser.py`: MIDI → 이벤트 시퀀스 (bar/position/pitch/duration/velocity)
- [ ] `tokenizer.py`: 토큰 사전 정의 및 encode/decode 구현
- [ ] 코드 진행 인코딩 (position 토큰과 정렬)
- [ ] 확장 화성(sus4, maj7, m7b5, min7) 처리 로직
- [ ] `augment.py`: key/bpm 증강
- [ ] **왕복 테스트**: `midi → tokens → midi` 후 노트 수/피치/타이밍 일치 검증
- [ ] 전체 데이터셋 토큰화 및 `.pt` 캐싱, train/valid 90:10 분할

**산출물**: 토큰화된 데이터셋, 토크나이저 유닛테스트
**DoD**: 무작위 100개 샘플에 대해 왕복 변환 오차 0

> 💡 이 Phase의 코드는 면접에서 "화성학 지식을 코드로 옮긴 부분"으로 직접 보여줄 수 있는 구간이므로, 주석과 docstring을 특히 신경 써서 작성.

---

### Phase 2 — 모델 구현 및 베이스라인 학습 (2주)

**목표**: 메타데이터 조건으로 단일 트랙을 생성하는 모델 확보

- [ ] `layers.py`: Multi-head attention, FFN, positional encoding 직접 구현
- [ ] `transformer.py`: Decoder-only 스택 조립, causal mask
- [ ] `train.py`: 학습 루프, gradient accumulation, mixed precision, 체크포인트 저장
- [ ] 소규모 오버피팅 테스트 (샘플 100개로 loss가 0에 수렴하는지 → 구현 검증)
- [ ] 전체 학습 실행, W&B에 loss curve 기록
- [ ] lr / d_model / max_seq_len 하이퍼파라미터 스윕 (최소 3회 실험)
- [ ] 첫 생성 샘플 청취 및 정성 평가

**산출물**: 학습된 체크포인트, W&B 실험 대시보드, 생성 샘플 5개
**DoD**: 지정한 key/코드 진행을 따르는 8마디 멜로디가 생성됨

---

### Phase 3 — 순차 트랙 생성 + Stage2 조합 (1.5주) ⭐

**목표**: 멀티트랙 완성곡 자동 생성 (선행연구 미해결 과제)

- [ ] `sampler.py`: top-k / nucleus 샘플링, 코드 토큰 주입
- [ ] `sequential.py`: 멜로디 생성 → 코드 추출 → track_role 교체 순차 생성 오케스트레이션
- [ ] `combiner.py` **(핵심)**:
  - [ ] 음역 충돌 검출 및 해소 (track_role별 pitch range 규칙 적용)
  - [ ] 수직 화성 검사 — 동시 발음 노트가 해당 코드의 스케일/코드톤에 속하는지
  - [ ] 불협화 임계 초과 시 해당 트랙 부분 리샘플링
  - [ ] 트랙별 velocity 밸런싱 (멜로디 우선)
- [ ] 조합 전/후 불협화 비율 비교 실험 (조합 로직의 효과 정량 입증)

**산출물**: 멀티트랙 MIDI 생성 함수, 조합 로직 효과 비교 표
**DoD**: 멜로디+반주+베이스 3트랙 이상이 화성 충돌 없이 합쳐진 8마디 곡 생성

> 📌 **면접 대비**: "왜 단순히 이어붙이지 않고 이런 로직이 필요한가"를 불협화 비율 수치로 설명할 수 있게 준비.

---

### Phase 4 — 화성 분석 · 전조 · 이조 모듈 (1주) ⭐

**목표**: 생성 결과를 음악 이론적으로 분석·변형하는 기능

- [ ] `analysis.py`: music21 기반 조성/화성 분석 래퍼
- [ ] **music21 기본 기능 확장** (차별화 구간):
  - [ ] 세컨더리 도미넌트 탐지
  - [ ] 논다이어토닉 코드 / 차용 화음 표기
  - [ ] 텐션(9th, 11th, 13th) 식별
- [ ] `transpose.py`: 이조 (전 트랙 동기 이조, 악기별 음역 초과 경고)
- [ ] `modulation.py` **(차별화)**: 단순 이조가 아닌 **피벗 코드 기반 전조 경로 계산**
  - [ ] 원조/목표조 공통 화음 탐색
  - [ ] 전조 연결부 코드 진행 제안
- [ ] `dissonance.py`: 불협화 검출 (Phase 3 조합기와 공유)

**산출물**: 분석 모듈, 분석 리포트 예시 (코드 네임 + 기능화성 표기)
**DoD**: 임의 생성곡에 대해 조성/코드 진행이 출력되고, C major → A minor 전조가 피벗 코드를 경유해 생성됨

---

### Phase 5 — 악보 렌더링 및 데모 배포 (1주)

**목표**: 결과물을 눈과 귀로 확인 가능한 형태로

- [ ] `to_musicxml.py`: 멀티트랙 MIDI → MusicXML (파트별 분리, 조표/박자표 반영)
- [ ] Colab에 MuseScore 4 headless 설치 스크립트 작성
- [ ] `to_score.py`: MusicXML → PNG/PDF 렌더링
- [ ] `to_audio.py`: FluidSynth + SoundFont로 wav 렌더링
- [ ] `gradio_app.py`: 메타데이터 입력 UI → 생성 → 악보 이미지 + 오디오 플레이어 출력
- [ ] HuggingFace Spaces 배포
- [ ] 데모 영상 촬영 (2~3분)

**산출물**: 배포된 데모 URL, 데모 영상, 샘플 악보 PNG
**DoD**: 링크 하나로 제3자가 곡을 생성하고 악보를 다운로드할 수 있음

---

### Phase 6 — 평가 및 실험 리포트 (1주) ⭐

**목표**: "잘 되는 것 같다"가 아니라 숫자로 입증

- [ ] `controllability.py`
  - [ ] **CP (pitch control)**: 지정 pitch range를 만족하는 노트 비율
  - [ ] **CV (velocity control)**: min/max velocity 범위 내 노트 비율
  - [ ] **CH (harmony control)**: 조성 스케일 또는 코드톤에 속하는 노트 비율 (불협화 아닌 비율)
- [ ] `diversity.py`
  - [ ] chroma 유사도 + groove 유사도 기반 pairwise distance
  - [ ] 동일 메타데이터로 10개 생성 후 평균 거리 산출
- [ ] **자체 확장 지표** (차별화):
  - [ ] 트랙 간 음역 중첩률
  - [ ] 코드 진행 준수율 (마디별)
  - [ ] track_role별 note density / note length 분포가 학습 데이터 분포와 일치하는지
- [ ] Ablation 실험 최소 2건:
  - [ ] track_role 조건 유무 비교
  - [ ] 확장 화성(sus4/maj7) 토큰 유무 비교
- [ ] 소규모 정성 평가 (음악 전공 지인 5~10명 대상 A/B 선호도 설문)
- [ ] `04_eval_report.ipynb`로 결과 표/그래프 정리

**산출물**: 평가 리포트, ablation 결과 표, 설문 결과
**DoD**: 모든 지표에 대해 수치가 산출되고 표로 정리됨

---

### Phase 7 — 편곡 기능 (스트레치, 1~2주)

**목표**: 동일 멜로디를 여러 스타일로 재편곡

- [ ] **MVP**: 멜로디·코드 고정 + genre/instrument/track_role만 교체하여 재생성
- [ ] 편곡 프리셋 정의 (예: 어쿠스틱 밴드 / 로파이 / 스트링 앙상블)
- [ ] Gradio UI에 "이 트랙 다시 편곡" 버튼 추가
- [ ] (선택) Transformer-VAE 계열 latent 보간 기반 스타일 트랜스퍼
- [ ] (선택) MusicGen melody-conditioning으로 오디오 품질 향상

**DoD**: 동일 멜로디에 대해 3가지 이상 구분 가능한 편곡 버전 생성

---

### Phase 8 — 문서화 및 포트폴리오화 (상시)

- [ ] `README.md`: 문제정의 → 접근 → 아키텍처 다이어그램 → 결과 → 데모 링크
- [ ] `docs/architecture.md`: 설계 의사결정 기록 (왜 심볼릭인가, 왜 REMI인가 등)
- [ ] `docs/experiment_log.md`: 실험 일지 (Notion 학습노트 DB와 동기화)
- [ ] 샘플 갤러리 (악보 PNG + mp3 + 메타데이터 조건 표기)
- [ ] 이력서/자소서용 3줄 요약 문장 작성
- [ ] (선택) 기술 블로그 포스팅 2~3편 — 토크나이저 설계 / Stage2 조합 로직 / 평가 지표 설계

---

## 7. 마일스톤 요약

| 주차 | Phase | 마일스톤 |
|---|---|---|
| W1 | 0 | 환경 세팅 완료, 데이터 확보 |
| W2~3 | 1 | 토크나이저 왕복 변환 성공 |
| W3~5 | 2 | **M1: 조건부 단일 트랙 생성 성공** |
| W5~6 | 3 | **M2: 멀티트랙 완성곡 자동 생성** |
| W7 | 4 | 화성 분석/전조 모듈 완성 |
| W8 | 5 | **M3: 데모 배포 + 악보 출력** |
| W9 | 6 | **M4: 평가 리포트 완성** |
| W10~11 | 7 | 편곡 기능 (스트레치) |
| 상시 | 8 | 문서화 |

> ⏱️ 시간이 부족해질 경우 **잘라낼 순서**: Phase 7 → Phase 4의 전조 고도화 → Lakh MIDI 사전학습 → K-indie 데이터 확장.
> **절대 자르면 안 되는 것**: Phase 2(직접 구현), Phase 3(Stage2), Phase 6(평가) — 이 셋이 포트폴리오의 뼈대.

---

## 8. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| Colab 세션 끊김으로 학습 유실 | 높음 | 매 N step Drive에 체크포인트 저장, 재개 로직 필수 구현 |
| 생성 결과가 음악적으로 어색함 | 높음 | 샘플링 파라미터 조정 → 데이터 증강 재검토 → 모델 크기 증대 순으로 대응 |
| 학습 데이터 라이선스 문제 | 중간 | ComMU 라이선스 조건 사전 확인, 상업적 사용 주장하지 않음, 포트폴리오는 비영리 명시 |
| MusicXML 변환 시 박자/조표 깨짐 | 중간 | music21 quantize 후 변환, 소절 단위 검증 스크립트 작성 |
| Stage2 조합 로직이 과도하게 복잡해짐 | 중간 | 규칙을 3단계(음역→화성→밸런스)로 제한, 그 이상은 v2로 이월 |
| K-indie 데이터 라벨링에 시간 과다 소요 | 중간 | 100샘플 상한 설정, 초과 시 Phase 7로 이월 |
| 범위 확장(scope creep) | 높음 | 위 "잘라낼 순서" 원칙 준수, 매주 회고 시 스코프 점검 |

---

## 9. 성공 기준

### 9.1 기술적 성공 기준

- [ ] 지정 메타데이터를 따르는 멀티트랙 곡 생성 (harmony control 0.95 이상 목표)
- [ ] 생성곡이 오선지 악보로 출력되어 사람이 연주 가능
- [ ] 정량 평가 지표 4종 이상이 리포트로 정리됨
- [ ] Ablation 2건 이상으로 설계 선택의 근거 제시

### 9.2 포트폴리오 성공 기준

- [ ] 데모 링크만으로 제3자가 결과물을 체험 가능
- [ ] README만 읽어도 문제정의–접근–결과가 3분 안에 파악됨
- [ ] "직접 만든 부분"과 "가져다 쓴 부분"이 명확히 구분되어 서술됨
- [ ] 면접에서 아키텍처 선택 이유를 5분간 설명할 수 있음

---

## 10. 참고 자료

| 자료 | 용도 |
|---|---|
| ComMU (NeurIPS 2022 D&B) — Pozalabs | 데이터셋, 메타데이터 설계, 평가 지표 |
| REMI / Pop Music Transformer (ACM MM 2020) | 토큰 표현 방식의 원형 |
| Music Transformer (ICLR 2019) | 심볼릭 생성 아키텍처 레퍼런스 |
| MMM (2020) | 멀티트랙 조건부 생성 비교군 |
| MuseMorphose (2021) | 스타일 트랜스퍼 (Phase 7 스트레치) |
| FIGARO (2022) | 세밀한 제어 기반 생성 비교군 |
| music21 documentation | 화성 분석/이조 API |
| audiocraft (MusicGen) | 오디오 렌더링 스트레치 |

---

## 변경 로그

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-09-03 | v0.1 | 최초 작성 |
| | | |
