import pygame
import sys
import random
from engine import GameManager

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Echoes of the Continuum — Infinite Dimension Survival")

    gm      = GameManager(screen)
    running = True

    while running:
        events = pygame.event.get()
        pygame.mouse.set_visible(gm.state == "MENU")

        for event in events:
            if event.type == pygame.QUIT:
                running = False

            if gm.state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                        gm.settings_open = not gm.settings_open
                        gm.settings_sel  = 0
                    elif event.key == pygame.K_1: gm.start_game("1")
                    elif event.key == pygame.K_2: gm.start_game("2")
                    elif event.key == pygame.K_3: gm.start_game("3")
                    elif event.key == pygame.K_4: gm.start_game("4")
                    elif event.key == pygame.K_5: gm.start_game("5")
                    elif event.key == pygame.K_6: gm.start_game("6")
                    elif event.key == pygame.K_r:
                        # 룰렛 시작
                        if not gm.roulette_active:
                            gm.roulette_active   = True
                            gm.roulette_timer    = 0
                            gm.roulette_result   = None
                            gm.roulette_flash    = 0
                            gm.roulette_idx      = random.randint(0, 5)
                            # 결과 미리 결정 (랜덤)
                            target = random.randint(0, 5)
                            # duration을 target에 맞게 조정 (정확히 그 칸에서 멈추도록)
                            gm._roulette_target = target
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    # 룰렛 버튼 클릭
                    roulette_btn = pygame.Rect(310, 492, 180, 38)
                    if roulette_btn.collidepoint(mx, my) and not gm.roulette_active:
                        gm.roulette_active = True
                        gm.roulette_timer  = 0
                        gm.roulette_result = None
                        gm.roulette_flash  = 0
                        gm.roulette_idx    = random.randint(0, 5)
                        gm._roulette_target = random.randint(0, 5)
                        break
                    # 룰렛 결과 → 바로 시작 버튼
                    if gm.roulette_result and gm.roulette_flash > 0:
                        start_btn = pygame.Rect(270, 540, 260, 38)
                        if start_btn.collidepoint(mx, my):
                            gm.start_game(gm.roulette_result)
                            break
                    chapter_ids = ["1","2","3","4","5","6"]
                    cols = 2
                    card_w, card_h = 340, 88
                    x_start, y_start, x_gap, y_gap = 60, 158, 360, 108
                    for i, cid in enumerate(chapter_ids):
                        row = i // cols; ci = i % cols
                        bx = x_start + ci * x_gap
                        by = y_start + row * y_gap
                        card = pygame.Rect(bx, by, card_w, card_h)
                        if card.collidepoint(mx, my):
                            gm.start_game(cid)
                            break

            elif gm.state == "DEATH":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    gm.state = "MENU"

            elif gm.state == "WIN":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    gm.state = "MENU"

        gm.update(events)
        gm.draw()
        gm.clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()