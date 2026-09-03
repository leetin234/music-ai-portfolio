# 설계 의사결정 기록

> "왜 이렇게 만들었는가"를 남기는 문서. 면접에서 그대로 쓰인다.

## 왜 오디오가 아니라 심볼릭(MIDI)인가

- 오디오 파형 생성은 데이터·연산량이 개인 프로젝트 범위를 넘어선다
  (MusicGen은 2만 시간 규모 학습)
- MIDI 이벤트 시퀀스는 "다음 토큰 예측" 문제로 환원되어 Transformer를 그대로 적용 가능
- 화성 이론 지식을 토큰 설계와 평가 지표에 직접 반영할 수 있다 ← 본 프로젝트의 차별화 축

## 왜 REMI 계열 표현인가

- MIDI-like 표현은 bar/position 토큰이 없어 마디 구조를 형성하지 못하고,
  코드 정보를 노트 시퀀스와 정렬할 수 없다
- 선행연구 주관평가에서 REMI 표현이 controllability/humanness/richness 전반에서 우위

## 왜 해상도 128인가

- 32/64/128 비교 실험에서 128이 humanness·richness 최고점
- 아르페지오, 스윙 리듬, 꾸밈음(트릴·앞꾸밈음·모르덴트) 표현에 고해상도가 필요
- 다만 어휘가 커져 controllability는 소폭 하락하는 트레이드오프가 있다

## 왜 track_role을 조건으로 두는가

- 악기만으로 트랙을 구분하면 "피아노를 반주로, 기타를 멜로디로" 같은
  저상관 조합을 만들 수 없다
- 같은 악기라도 역할에 따라 note density, 음역, 리듬이 달라진다

## 아직 정하지 못한 것

- [ ] positional encoding: sinusoidal vs learned
- [ ] 증강 채택 여부 (controllability↑ / diversity↓ 트레이드오프)
- [ ] Stage2 조합에서 리샘플링 임계값
