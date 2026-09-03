"""이벤트 시퀀스 ↔ 정수 토큰 id 변환.

Phase 1 구현 대상. **이 프로젝트의 핵심 산출물 중 하나.**

면접에서 "화성학 지식을 코드로 옮긴 부분"으로 직접 보여줄 코드이므로
docstring과 주석을 충실히 작성할 것.

시퀀스 구조:
    [BPM][KEY][TIME_SIG][PITCH_RANGE][NUM_MEASURES][INST]
    [GENRE][MIN_VEL][MAX_VEL][TRACK_ROLE][RHYTHM]
    [BAR][POSITION][CHORD]...[EOS]
"""

from typing import List
import yaml


class REMITokenizer:
    """REMI 확장형 토크나이저.

    원형인 REMI 대비 차이점:
        1. 메타데이터 11종을 시퀀스 앞에 prepend
        2. 확장 화성(sus4/maj7/min7/m7b5) 포함 → 코드 이벤트 108종
        3. tempo 토큰 제거
        4. 해상도를 32분음표 → 128분음표로 상향
    """

    def __init__(self, config_path: str = "configs/tokenizer.yaml"):
        with open(config_path, encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f)
        # TODO(Phase 1): 사전 구축
        self.token2id = {}
        self.id2token = {}

    def build_vocab(self) -> None:
        """설정 파일로부터 토큰 사전을 구축한다.

        TODO(Phase 1): 각 메타데이터의 첫 값은 unknown 토큰으로 예약.
        """
        raise NotImplementedError

    def encode(self, events, metadata) -> List[int]:
        raise NotImplementedError

    def decode(self, ids: List[int]):
        raise NotImplementedError

    @property
    def vocab_size(self) -> int:
        return len(self.token2id)
