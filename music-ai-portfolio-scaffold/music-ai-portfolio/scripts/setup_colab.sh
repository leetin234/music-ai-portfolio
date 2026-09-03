#!/usr/bin/env bash
# ============================================================
# Colab 시스템 패키지 세팅
# 사용법: !bash scripts/setup_colab.sh
# ============================================================
set -e

echo "▶ apt 패키지 설치 (fluidsynth, soundfont, musescore 의존성)"
apt-get -qq update
apt-get -qq install -y \
    fluidsynth \
    fluid-soundfont-gm \
    libfluidsynth3 \
    xvfb \
    libegl1 \
    libopengl0 \
    libasound2-dev \
    > /dev/null

echo "▶ MuseScore 4 (AppImage) 다운로드"
# 악보 렌더링용. 최신 릴리스 URL은 https://github.com/musescore/MuseScore/releases 에서 확인.
# AppImage는 Colab에서 --appimage-extract 방식으로 실행하는 것이 안정적이다.
MUSESCORE_DIR="/opt/musescore"
mkdir -p "$MUSESCORE_DIR"
if [ ! -f "$MUSESCORE_DIR/squashfs-root/AppRun" ]; then
    echo "  ⚠ MuseScore AppImage를 수동으로 배치해야 합니다."
    echo "    1) https://github.com/musescore/MuseScore/releases 에서 x86_64 AppImage URL 확인"
    echo "    2) wget -O $MUSESCORE_DIR/mscore.AppImage <URL>"
    echo "    3) cd $MUSESCORE_DIR && chmod +x mscore.AppImage && ./mscore.AppImage --appimage-extract"
    echo "    → Phase 5(악보 렌더링)에서 필요. Phase 0~4는 이것 없이 진행 가능."
fi

echo "▶ SoundFont 위치 확인"
ls -la /usr/share/sounds/sf2/ 2>/dev/null || echo "  (sf2 경로 확인 필요)"

echo "✅ 시스템 패키지 세팅 완료"
