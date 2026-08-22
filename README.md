# Dimension Fight

차원을 넘어, 별을 쫓아 — C++ · SDL2 기반 2D 차원 액션 슈팅 게임.
물리 차원과 공허 차원을 자유롭게 넘나들며 싸우는 온라인 멀티플레이 지원 게임입니다.

- 저장소: https://github.com/kimneche0419-rgb/dimension_fight
- 발표 자료: `Dimension_Fight_프레젠테이션.pptx` / `.pdf`

## 다운로드

### Windows — CMD (명령 프롬프트)

```cmd
git clone https://github.com/kimneche0419-rgb/dimension_fight.git
cd dimension_fight
```

Git이 없다면 zip으로 받기:

```cmd
curl -L -o dimension_fight.zip https://github.com/kimneche0419-rgb/dimension_fight/archive/refs/heads/main.zip
tar -xf dimension_fight.zip
```

### Windows — PowerShell

```powershell
git clone https://github.com/kimneche0419-rgb/dimension_fight.git
Set-Location dimension_fight
```

Git이 없다면 zip으로 받기:

```powershell
Invoke-WebRequest -Uri "https://github.com/kimneche0419-rgb/dimension_fight/archive/refs/heads/main.zip" -OutFile "dimension_fight.zip"
Expand-Archive -Path "dimension_fight.zip" -DestinationPath "."
```

### macOS

```bash
git clone https://github.com/kimneche0419-rgb/dimension_fight.git
cd dimension_fight
```

Git이 없다면 zip으로 받기:

```bash
curl -L -o dimension_fight.zip https://github.com/kimneche0419-rgb/dimension_fight/archive/refs/heads/main.zip
unzip dimension_fight.zip
```

### Linux

```bash
git clone https://github.com/kimneche0419-rgb/dimension_fight.git
cd dimension_fight
```

Git이 없다면 zip으로 받기:

```bash
curl -L -o dimension_fight.zip https://github.com/kimneche0419-rgb/dimension_fight/archive/refs/heads/main.zip
unzip dimension_fight.zip
# unzip이 없다면: sudo apt install unzip  (Debian/Ubuntu)
```

### curl 한 줄 명령 (모든 OS 공통)

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
