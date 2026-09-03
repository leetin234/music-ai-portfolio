# 조건부 멀티트랙 심볼릭 음악 생성 시스템

> 사용자가 지정한 음악적 메타데이터(장르·조성·코드 진행·트랙 역할)를 조건으로
> **멜로디를 먼저 생성하고 그 위에 반주·베이스·패드를 순차적으로 쌓아 완성곡을 만드는**
> 심볼릭 음악 생성 시스템. 결과물은 화성 분석·전조를 거쳐 오선지 악보와 오디오로 출력됩니다.

🚧 **개발 중** — 현재 Phase 0 (환경 세팅)

---

## 데모

| | |
|---|---|
| 데모 | (Phase 5에서 HuggingFace Spaces 링크 추가) |
| 샘플 | [docs/samples/](docs/samples/) |
| 개발계획서 | [docs/dev_plan.md](docs/dev_plan.md) |

---

## 문제 정의

기준 선행연구인 **ComMU** (Pozalabs, NeurIPS 2022)는 12종 메타데이터로 조건부
음악 생성을 수행하지만, 두 가지를 한계로 남겨두었습니다.

| 선행연구의 한계 | 본 프로젝트의 대응 |
|---|---|
| **Stage2(트랙 조합) 미구현** — 트랙별 생성까지만 다루고, 완성곡으로 합치는 단계는 전문가 수작업에 의존 | Stage2를 화성 충돌 방지 로직 기반으로 **자동화** |
| **장르·리듬 편중** — genre 2종(new age/cinematic), 4/4·standard에 크게 쏠림 | K-indie 계열 메타데이터를 **신규 정의**하고 직접 라벨링해 확장 |

여기에 더해, 대부분의 선행 시스템이 MIDI/오디오만 출력하는 것과 달리
**연주 가능한 오선지 악보 출력**과 **화성 분석·전조 기능**을 갖춘 실사용 도구를 지향합니다.

---

## 아키텍처

```
사용자 입력 (장르/조성/BPM/코드 진행)
        ↓
조건 토큰 인코딩 (REMI 확장형, 확장 화성 포함)
        ↓
Track Generator (Decoder-only Transformer, 직접 구현)
        ↓  track_role=main_melody
   멜로디 생성 → 코드 진행 추출
        ↓  track_role 교체하여 순차 생성
   반주 · 베이스 · 패드 · 리프
        ↓
Stage2 조합기 (음역 충돌 해소 / 불협화 검출 / 밸런싱)
        ↓
┌──────────────┬──────────────┬──────────────┐
│ 화성 분석     │ 편곡         │ 출력          │
│ 전조 · 이조   │ 스타일 변형   │ 악보/MIDI/오디오│
└──────────────┴──────────────┴──────────────┘
```

---

## 기술 스택

**모델링** PyTorch (Transformer 직접 구현)
**MIDI** miditoolkit, pretty_midi
**음악 이론** music21 + 자체 확장 (세컨더리 도미넌트, 피벗 코드 전조)
**악보** MusicXML, MuseScore 4
**오디오** FluidSynth + SoundFont
**실험 관리** Weights & Biases
**데모** Gradio, HuggingFace Spaces
**환경** Google Colab Pro+ (A100)

---

## 프로젝트 구조

```
├── configs/      설정 (모델 · 토크나이저)
├── data/         MIDI 파싱 · 토크나이저 · 증강
├── model/        Transformer 아키텍처 · 학습
├── generate/     샘플링 · 순차 생성 · Stage2 조합  ⭐
├── theory/       화성 분석 · 전조 · 이조           ⭐
├── render/       MusicXML · 악보 · 오디오
├── eval/         Controllability · Diversity
├── app/          Gradio 데모
├── notebooks/    Colab 실행용
└── docs/         설계 기록 · 실험 일지 · 샘플
```

---

## 시작하기

```bash
# 1. Colab에서 notebooks/00_setup.ipynb 실행
#    - GPU 확인, Drive 마운트, 데이터 다운로드, W&B 연동

# 2. 로컬에서 개발할 경우
pip install -r requirements.txt
bash scripts/setup_colab.sh   # 시스템 패키지 (fluidsynth 등)
```

---

## 진행 상황

- [x] **Phase 0** 환경 세팅 및 데이터 확보
- [ ] **Phase 1** 데이터 파이프라인 & 토크나이저
- [ ] **Phase 2** Transformer 구현 및 베이스라인 학습
- [ ] **Phase 3** 순차 트랙 생성 + Stage2 조합 ⭐
- [ ] **Phase 4** 화성 분석 · 전조 · 이조 ⭐
- [ ] **Phase 5** 악보 렌더링 및 데모 배포
- [ ] **Phase 6** 평가 및 실험 리포트 ⭐
- [ ] **Phase 7** 편곡 기능 (스트레치)

---

## 직접 구현한 부분 / 활용한 자산

투명성을 위해 명확히 구분합니다.

**직접 설계·구현**
토크나이저 및 토큰 스키마 · Transformer 아키텍처 · 조건화 방식 ·
Stage2 트랙 조합 로직 · 화성 분석 확장(세컨더리 도미넌트, 피벗 코드 전조) ·
평가 지표 설계 및 측정 코드

**기존 자산 활용**
ComMU 데이터셋 · REMI 표현 방식(확장하여 사용) · music21 · MuseScore · FluidSynth

---

## 라이선스 및 출처

본 프로젝트는 **비상업적 포트폴리오 목적**으로 제작되었습니다.

학습 데이터로 사용한 **ComMU 데이터셋**은 POZAlabs가
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)으로 배포한 것입니다.
동일 조건 변경 허락(ShareAlike) 조항에 따라 본 저장소의 파생 결과물도 동일 라이선스를 따릅니다.

- ComMU: *ComMU: Dataset for Combinatorial Music Generation*, NeurIPS 2022 Datasets & Benchmarks Track
- REMI: *Pop Music Transformer*, ACM Multimedia 2020
