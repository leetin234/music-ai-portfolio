# Conversational Singing AI — MVP v0.2

## 1. Product thesis

대화형 AI가 텍스트/음성으로만 반응하는 것을 넘어, **상황에 맞을 때 짧은 노래를 직접 만들어 불러주는 경험**을 만든다.

핵심 연구 질문:

> When should a conversational AI sing, and how should conversation context become a short personalized song?

이 프로젝트에서 음악은 별도 생성 기능이 아니라 **AI 캐릭터의 감정 표현 수단**이다.

---

## 2. MVP user experience

예시:

```text
User:
오늘 면접 망해서 기분이 별로야.

AI:
아이고... 오늘 고생했네.
잠깐만, 짧게 하나 불러줄게.

♪ 오늘 하루 조금 꼬였어도
내일은 또 모르잖아 ♪

AI:
오늘은 여기까지만 생각하고 좀 쉬자.
```

### MVP 성공 기준

한 번의 사용자 대화 입력에 대해:

1. 노래가 적절한 상황인지 판단
2. 2~4줄의 짧은 가사 생성
3. 4마디 melody + chord 생성
4. singing voice audio 생성
5. 대화 응답으로 자연스럽게 복귀

목표 노래 길이: **5~15초**

---

## 3. v0.2 architecture

```text
Conversation Input
      ↓
Context Analyzer
- emotion
- intent
- relationship context
      ↓
Song Trigger
- sing / do_not_sing
- reason
- song_type
      ↓
Song Planner
- lyrics
- key
- bpm
- mood
- chord progression
      ↓
Music Engine (existing music_ai_dev)
- melody
- chord
- 4 bars
      ↓
Singing Voice Synthesis
- lyrics + MIDI/notes
- licensed/open singer model only
      ↓
Audio
      ↓
Conversation Resume
```

---

## 4. Scope decisions

### Must have

- text conversation
- song trigger decision
- short lyric generation
- 4-bar symbolic melody generation
- singing voice synthesis
- WAV output
- simple demo UI
- experiment log

### Existing music_ai_dev assets retained

- MIDI parser
- tokenizer
- REMI-style representation
- conditional Transformer
- harmony evaluation
- later Stage2 multi-track logic

### Deferred

- celebrity / artist voice cloning
- custom singing voice training
- real-time full duplex voice conversation
- video avatar
- full song generation
- 3+ minute music
- large fan-memory system
- production payment/subscription

---

## 5. Singing synthesis strategy

MVP에서는 singing voice model을 직접 학습하지 않는다.

우선순위:

1. **OpenVPI DiffSinger** inference integration
2. NNSVS as research fallback
3. temporary deterministic/mock renderer only if integration blocks vertical-slice development

Voicebank/model은 반드시 라이선스가 명확한 공개 모델 또는 본인이 사용할 권리가 있는 음성을 사용한다.

목표는 voice cloning 자체가 아니라:

```text
conversation context
→ music plan
→ notes + lyrics
→ singing audio
```

end-to-end 경험 검증이다.

---

## 6. Development order

### M0 — Singing spike

고정된 4마디 melody + 고정 lyrics를 singing WAV로 출력한다.

DoD:
- Python command 또는 script 한 번으로 WAV 생성
- repo에 모델 파일 자체를 커밋하지 않음
- 모델/voicebank license 출처 문서화

### M1 — Song planner

사용자 대화를 받아 다음 JSON 생성:

```json
{
  "should_sing": true,
  "song_type": "comfort",
  "mood": "warm",
  "bpm": 76,
  "key": "D_major",
  "bars": 4,
  "lyrics": ["...", "..."]
}
```

DoD:
- 일반 질문에는 should_sing=false
- 축하/위로/장난 등 정의된 상황에서만 true

### M2 — Existing music engine integration

Song Planner의 조건을 music generator로 전달한다.

DoD:
- 4-bar MIDI 생성
- key/bpm 조건 반영
- lyrics syllable/note alignment에 사용할 note events 제공

### M3 — Lyrics-note alignment

가사의 음절과 note sequence를 연결한다.

DoD:
- 최소 한국어 짧은 문장 지원
- overflow/underflow 처리 규칙 존재
- 테스트 포함

### M4 — End-to-end song turn

```text
conversation
→ trigger
→ lyrics
→ music
→ singing WAV
→ resume message
```

DoD:
- 하나의 함수/CLI에서 end-to-end 실행
- 5~15초 내외 결과 생성

### M5 — Demo

간단한 Web UI에서:
- 대화 입력
- AI 텍스트 응답
- song turn 발생 시 audio player 표시
- 생성 조건 표시

---

## 7. Core evaluation

기존 음악 생성 지표 외에 Conversational Singing 지표를 추가한다.

- Song Trigger Precision
- Context–Lyrics Relevance
- Mood–Music Consistency
- Lyric–Note Alignment Error
- Singing synthesis success rate
- end-to-end latency
- subjective preference: normal response vs singing response

---

## 8. Portfolio positioning

기존 프로젝트 설명:

> Conditional multi-track symbolic music generation

v0.2 설명:

> **A context-aware conversational AI that decides when to sing, composes a short personalized song, synthesizes the singing voice, and returns naturally to conversation.**

직접 설계/구현:
- song trigger policy
- conversation → music condition mapping
- symbolic music generator
- harmony-aware evaluation
- lyric-note alignment
- end-to-end orchestration

활용:
- LLM API/local LLM for language planning
- Open-source singing voice synthesis engine
- existing music libraries

---

## 9. Immediate first target

**M0만 먼저 성공시킨다.**

첫 질문은 이것 하나다:

> 이 repo에서 고정된 lyrics + MIDI/notes를 넣으면 실제 singing WAV가 나오는가?

이게 성공한 뒤에 conversation/LLM과 기존 Transformer를 연결한다.
