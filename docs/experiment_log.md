# 실험 일지

> Notion "music_ai"와 동기화. 여기가 원본, Notion이 사본.

## 기록 형식

각 실험마다 아래 항목을 남긴다.

| 항목 | 내용 |
|---|---|
| 날짜 | |
| Phase | |
| 목적 | 무엇을 확인하려 했는가 |
| 변경 사항 | 이전 실험 대비 무엇을 바꿨는가 |
| 결과 | 수치 |
| 해석 | 왜 그런 결과가 나왔다고 보는가 |
| 다음 액션 | |

---

## 2026-XX-XX — Phase 0 환경 세팅

- **목적**: Colab 환경 검증 및 데이터 확보
- **결과**: (00_setup.ipynb 마지막 셀 출력을 붙여넣기)
- **다음 액션**: Phase 1 착수


## Phase 0 세팅 완료 — 2026-09-03 06:35

| 항목 | 값 |
|---|---|
| GPU | Tesla T4 |
| VRAM | 14.6 GB |
| 권장 precision | bf16 |
| Python | 3.13.15 |
| torch | 2.11.0+cu128 |
| 학습 샘플 수 | 11144 |
| 데이터 경로 | /content/drive/MyDrive/music-ai-portfolio/data/raw |

### 다음 액션
- [ ] configs/base.yaml의 precision을 `bf16`로 확인/수정
- [ ] max_seq_len이 충분한지 위 노트 수 통계로 판단
- [ ] commu_meta.csv의 실제 컬럼명을 configs/tokenizer.yaml에 반영
- [ ] Phase 1 착수: data/parser.py 구현
---
