# Dimension Fight

차원을 넘어, 별을 쫓아 — C++ · SDL2 기반 2D 차원 액션 슈팅 게임.
물리 차원과 공허 차원을 자유롭게 넘나들며 싸우는 온라인 멀티플레이 지원 게임입니다.

- 저장소: https://github.com/kimneche0419-rgb/dimension_fight
- 발표 자료: `Dimension_Fight_프레젠테이션.pptx` / `.pdf`

## 다운로드

[![Download ZIP](https://img.shields.io/badge/⬇_Download-ZIP-00e5ff?style=for-the-badge)](https://github.com/kimneche0419-rgb/dimension_fight/archive/refs/heads/main.zip)

또는 터미널 한 줄 (Mac / Linux / Windows 공통, git만 있으면 됨):

```bash
git clone https://github.com/kimneche0419-rgb/dimension_fight.git
```

Git이 없다면 curl 한 줄로 압축까지 자동 해제 (Mac / Linux / WSL):

```bash
curl -L https://github.com/kimneche0419-rgb/dimension_fight/archive/refs/heads/main.tar.gz | tar -xz
```

## 빌드 (Windows)

MSYS2 MinGW64 + SDL2가 설치되어 있어야 합니다.

```bash
cd dimension_fight_cpp
bash build_msys2.sh
```

빌드 산출물은 `dimension_fight_cpp/build/`에 생성됩니다. `run.bat` 또는
`DimensionFightLauncher.exe`로 실행하세요.
