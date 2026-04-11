import pygame
import sys
from engine import GameManager

def main():
    pygame.init()
    # 원상 복귀: 고해상도 지원 없이 800x600 기본 창 모드
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Paradox Survival: Neon Chronicles")

    gm = GameManager(screen)
    running = True

    while running:
        events = pygame.event.get()
        # 마우스 가시성 관리
        pygame.mouse.set_visible(gm.state in ("MENU", "SHOP", "COLOR_SELECT"))

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            # 전역 키보드 단축키 처리
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
                    if gm.state == "PLAYING":
                        gm.settings_open = not gm.settings_open
                    elif gm.state in ("SHOP", "COLOR_SELECT"):
                        gm.state = "MENU"

        # 모든 상태별 로직 및 입력 처리는 GameManager.update에서 수행
        gm.update(events)
        gm.draw()
        gm.clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()