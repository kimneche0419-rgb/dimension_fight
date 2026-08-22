# Dimension Fight

차원을 넘어, 별을 쫓아 — C++ · SDL2 기반 2D 차원 액션 슈팅 게임.
물리 차원과 공허 차원을 자유롭게 넘나들며 싸우는 온라인 멀티플레이 지원 게임입니다.

- 저장소: https://github.com/kimneche0419-rgb/dimension_fight
- 발표 자료: `Dimension_Fight_프레젠테이션.pptx` / `.pdf`

## 설치 (Windows — 일반 프로그램처럼)

다른 프로그램들과 똑같이 설치 마법사로 설치됩니다. Program Files에 설치되고,
시작 메뉴/바탕화면 바로가기가 생기며, "설정 > 앱"에서 그냥 제거할 수 있습니다.

1. `installer.iss`로 `DimensionFight_Setup.exe`를 빌드하거나(아래 참고), 배포된 설치 파일을 받습니다.
2. `DimensionFight_Setup.exe` 더블클릭 → 안내에 따라 설치.
3. 설치 완료 후 바로 게임 실행, 이후엔 바탕화면/시작 메뉴 아이콘으로 실행.

설치 프로그램 직접 빌드 (Windows, [Inno Setup](https://jrsoftware.org/isinfo.php) 필요):

```powershell
ISCC.exe installer.iss
```

`installer_output\DimensionFight_Setup.exe`가 생성됩니다.

## 소스 다운로드 (개발/빌드용)

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
