# -*- coding: utf-8 -*-
"""Dimension Fight 네온 로딩 화면 런처.

콘솔창 대신 그래픽 스플래시를 띄우고, local_proxy.exe를 창 없이
백그라운드로 시작한 뒤 게임을 실행한다. 게임이 종료되면 프록시도
함께 정리한다.
"""
import os
import random
import subprocess
import sys
import time
import tkinter as tk

# 배경/전경 색상 (게임의 네온 테마)
BG = "#0a0e1a"
NEON_CYAN = "#00e5ff"
NEON_MAGENTA = "#ff2bd6"
NEON_YELLOW = "#ffe14d"
DIM_TEXT = "#8b93b0"
BAR_TRACK = "#1c2340"

# PyInstaller exe로 빌드된 경우 실행 파일 기준, 개발 중에는 이 파일 기준
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # 소스 위치(dimension_fight_cpp/)에서 실행하면 build/를 기준으로 삼는다
    candidate = os.path.join(BASE_DIR, "build")
    if os.path.isfile(os.path.join(candidate, "DimensionFight.exe")):
        BASE_DIR = candidate

PROXY_EXE = os.path.join(BASE_DIR, "local_proxy.exe")
GAME_EXE = os.path.join(BASE_DIR, "DimensionFight.exe")
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")

CREATE_NO_WINDOW = 0x08000000  # 콘솔창 없이 자식 프로세스 실행

LOADING_MESSAGES = [
    "차원의 문을 여는 중...",
    "네온 파티클 충전 중...",
    "애니 과일을 세척하는 중...",
    "보스의 아침 커피를 내리는 중...",
    "전설의 무기에 먼지를 터는 중...",
    "별들을 다시 배열하는 중...",
    "차원술사를 깨우는 중...",
    "세이브 데이터를 점검하는 중...",
    "랙 없는 우주를 기원하는 중...",
    "불꽃놀이 장치를 점검하는 중...",
    "몹들에게 오늘의 대사를 배분하는 중...",
    "우주 청소부를 파견하는 중...",
]

TIPS = [
    "팁: 위험할 땐 대시!",
    "팁: 보스 패턴을 외우면 숨 쉴 틈이 보여요",
    "팁: 과일은 조합이 핵심",
    "팁: 죽어도 절망하지 말기 — 차원은 무한하다",
    "팁: 친구와 함께하면 두 배로 재밌어요",
    "팁: 골드는 아끼는 자가 부자 된다",
]

LOAD_SECONDS = 3.2   # 로딩 연출 시간
FPS_MS = 30          # 애니메이션 주기


class NeonSplash:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dimension Fight")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.geometry("560x380")
        if os.path.isfile(ICON_PATH):
            try:
                self.root.iconbitmap(ICON_PATH)
            except Exception:
                pass

        self.canvas = tk.Canvas(self.root, width=560, height=380,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        # 창을 화면 가운데로
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

        self.stars = []
        for _ in range(70):
            self.stars.append(self._new_star(random.randint(0, 560)))

        self.start_time = time.time()
        self.progress = 0.0
        self.message = random.choice(LOADING_MESSAGES)
        self.tip = random.choice(TIPS)
        self.next_message_at = 0.0
        self.finished = False
        self.error = None
        self.game_proc = None

        self.proxy_proc = self._start_proxy()

        self.root.after(FPS_MS, self._tick)
        self.root.after(int(LOAD_SECONDS * 1000), self._launch_game)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- 별 애니메이션 ----------
    def _new_star(self, x):
        depth = random.choice([1, 2, 3])
        return {
            "x": x,
            "y": random.randint(0, 380),
            "depth": depth,
            "color": random.choice([NEON_CYAN, NEON_MAGENTA, NEON_YELLOW,
                                    "#ffffff", "#ffffff"]),
        }

    def _draw_frame(self):
        c = self.canvas
        c.delete("all")

        # 별들: 깊이에 따라 속도/크기 다르게 흐른다
        for s in self.stars:
            s["y"] += s["depth"] * 1.4
            s["x"] -= s["depth"] * 0.5
            if s["y"] > 380 or s["x"] < 0:
                ns = self._new_star(random.randint(560, 640))
                s.update(ns)
            size = s["depth"]
            c.create_oval(s["x"] - size, s["y"] - size,
                          s["x"] + size, s["y"] + size,
                          fill=s["color"], outline="")

        # 타이틀 글로우 (여러 겹의 오프셋 텍스트)
        tx, ty = 280, 92
        for dx, dy, color in [(0, 0, NEON_MAGENTA), (-2, 0, NEON_CYAN),
                              (2, 0, NEON_CYAN), (0, -2, NEON_MAGENTA),
                              (0, 2, NEON_CYAN)]:
            c.create_text(tx + dx, ty + dy, text="DIMENSION FIGHT",
                          font=("맑은 고딕", 30, "bold"), fill=color)
        c.create_text(tx, ty, text="DIMENSION FIGHT",
                      font=("맑은 고딕", 30, "bold"), fill="#ffffff")

        # 부제
        c.create_text(280, 130, text="— 차원을 넘어, 별을 쫓아 —",
                      font=("맑은 고딕", 12), fill=DIM_TEXT)

        # 진행 바
        bar_x0, bar_y0, bar_w, bar_h = 90, 250, 380, 16
        c.create_rectangle(bar_x0 - 2, bar_y0 - 2,
                           bar_x0 + bar_w + 2, bar_y0 + bar_h + 2,
                           outline=NEON_CYAN, width=1)
        c.create_rectangle(bar_x0, bar_y0,
                           bar_x0 + bar_w, bar_y0 + bar_h,
                           fill=BAR_TRACK, outline="")
        fill_w = int(bar_w * self.progress)
        if fill_w > 0:
            c.create_rectangle(bar_x0, bar_y0,
                               bar_x0 + fill_w, bar_y0 + bar_h,
                               fill=NEON_CYAN, outline="")
            # 바 끝의 반짝이
            c.create_oval(bar_x0 + fill_w - 4, bar_y0 - 3,
                          bar_x0 + fill_w + 4, bar_y0 + bar_h + 3,
                          fill="#ffffff", outline="")

        # 진행률 텍스트
        c.create_text(280, 285,
                      text=f"{self.message}  ({int(self.progress * 100)}%)",
                      font=("맑은 고딕", 11), fill="#dde3f5")

        # 팁 (하단)
        c.create_text(280, 322, text=self.tip,
                      font=("맑은 고딕", 10), fill=DIM_TEXT)

        # 하단 브랜드 라인
        c.create_text(280, 355, text="DIMENSION FIGHT  ·  Standalone Client",
                      font=("맑은 고딕", 8), fill="#3d4566")

    # ---------- 상태 갱신 ----------
    def _tick(self):
        if self.finished:
            return

        elapsed = time.time() - self.start_time
        self.progress = min(1.0, elapsed / LOAD_SECONDS)

        if elapsed >= self.next_message_at:
            self.message = random.choice(LOADING_MESSAGES)
            self.next_message_at = elapsed + 0.7

        self._draw_frame()
        self.root.after(FPS_MS, self._tick)

    # ---------- 프로세스 관리 ----------
    def _start_proxy(self):
        if not os.path.isfile(PROXY_EXE):
            self.error = "local_proxy.exe 를 찾을 수 없어요!"
            return None
        try:
            return subprocess.Popen(
                [PROXY_EXE], cwd=BASE_DIR,
                creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            self.error = f"프록시 시작 실패: {e}"
            return None

    def _launch_game(self):
        self.finished = True

        if not os.path.isfile(GAME_EXE):
            self.message = "DimensionFight.exe 를 찾을 수 없어요!"
            self.progress = 1.0
            self._draw_frame()
            self.root.after(4000, self.root.destroy)
            return

        self.canvas.delete("all")
        self.canvas.create_text(280, 180, text="출격!",
                                font=("맑은 고딕", 44, "bold"),
                                fill=NEON_YELLOW)
        self.canvas.create_text(280, 240, text="차원으로 이동합니다...",
                                font=("맑은 고딕", 12), fill="#dde3f5")

        game_proc = subprocess.Popen([GAME_EXE], cwd=BASE_DIR)
        # 게임 프로세스를 기억해두면 mainloop 종료 후 종료를 기다렸다가
        # 프록시를 정리한다 (run() 참고).
        self.game_proc = game_proc

        self.root.after(600, self.root.destroy)

    def _kill_proxy(self):
        """프록시를 프로세스 트리째로 종료한다.

        local_proxy.exe는 PyInstaller onefile이라 bootstrapper와 실제
        워커가 별도 프로세스로 떠 있어서, terminate()만 호출하면 워커가
        살아남는다. Windows에서는 taskkill /T로 트리 전체를 정리한다.
        """
        if not self.proxy_proc or self.proxy_proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(self.proxy_proc.pid), "/T", "/F"],
                    creationflags=CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.proxy_proc.terminate()
        except Exception:
            pass

    def _on_close(self):
        self.finished = True
        self._kill_proxy()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        # 스플래시가 닫힌 뒤에도 프로세스는 살아서 게임 종료를 지켜본다.
        # 게임이 끝나면 백그라운드 프록시를 함께 정리한다.
        game_proc = getattr(self, "game_proc", None)
        if game_proc is not None:
            try:
                game_proc.wait()
            except Exception:
                pass
            time.sleep(1.0)
        self._kill_proxy()


if __name__ == "__main__":
    NeonSplash().run()
