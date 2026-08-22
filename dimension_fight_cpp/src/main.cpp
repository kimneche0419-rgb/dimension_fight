#include <SDL.h>
#include <SDL_ttf.h>
#include <SDL_mixer.h>
#include <SDL_image.h>
#include <cstdio>
#include "game.h"

int main(int argc, char* argv[]) {
    (void)argc; (void)argv;

    // ── SDL Init ──
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_TIMER) < 0) {
        SDL_Log("SDL_Init failed: %s", SDL_GetError());
        return 1;
    }

    if (IMG_Init(IMG_INIT_PNG) == 0) {
        SDL_Log("IMG_Init warning: %s", IMG_GetError());
    }

    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "1");

    // ── Window ──
    SDL_Window* window = SDL_CreateWindow(
        "Dimension Fight: Paradox Survival",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        SCREEN_W, SCREEN_H,
        SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE
    );
    if (!window) {
        SDL_Log("SDL_CreateWindow failed: %s", SDL_GetError());
        return 1;
    }

    // 창/작업 표시줄 아이콘 설정 — icon.ico 로드에 실패하면
    // exe에 임베드된 리소스 아이콘(resource.rc)이 대신 쓰인다.
    SDL_Surface* iconSurf = IMG_Load("icon.ico");
    if (!iconSurf) iconSurf = IMG_Load("assets/icon.ico");
    if (iconSurf) {
        SDL_SetWindowIcon(window, iconSurf);
        SDL_FreeSurface(iconSurf);
    }

    // ── Renderer ──
    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1,
        SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!renderer) {
        SDL_Log("SDL_CreateRenderer failed: %s", SDL_GetError());
        return 1;
    }

    // Virtual screen texture for resolution-independent rendering
    SDL_Texture* virtualScreen = SDL_CreateTexture(renderer,
        SDL_PIXELFORMAT_RGBA8888, SDL_TEXTUREACCESS_TARGET,
        SCREEN_W, SCREEN_H);
    if (!virtualScreen) {
        SDL_Log("Failed to create virtual screen: %s", SDL_GetError());
        return 1;
    }

    // ── Game Init ──
    Game game;
    // Set render target to virtual screen for game init
    SDL_SetRenderTarget(renderer, virtualScreen);
    if (!game.init(renderer)) {
        SDL_Log("Game init failed!");
        return 1;
    }

    // ── Main Loop ──
    bool running = true;
    Uint32 lastTick = SDL_GetTicks();

    while (running) {
        Uint32 frameStart = SDL_GetTicks();

        // ── Collect Events ──
        SDL_Event events[64];
        int eventCount = 0;

        // Get current window size for coordinate translation
        int winW, winH;
        SDL_GetWindowSize(window, &winW, &winH);
        float scale = std::min((float)winW / SCREEN_W, (float)winH / SCREEN_H);
        int newW = (int)(SCREEN_W * scale);
        int newH = (int)(SCREEN_H * scale);
        int offsetX = (winW - newW) / 2;
        int offsetY = (winH - newH) / 2;

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) {
                running = false;
                continue;
            }

            // Translate mouse coordinates to virtual screen space
            if (e.type == SDL_MOUSEMOTION) {
                e.motion.x = (int)std::max(0.0f, std::min(799.0f, (e.motion.x - offsetX) / scale));
                e.motion.y = (int)std::max(0.0f, std::min(599.0f, (e.motion.y - offsetY) / scale));
            }
            if (e.type == SDL_MOUSEBUTTONDOWN || e.type == SDL_MOUSEBUTTONUP) {
                e.button.x = (int)std::max(0.0f, std::min(799.0f, (e.button.x - offsetX) / scale));
                e.button.y = (int)std::max(0.0f, std::min(599.0f, (e.button.y - offsetY) / scale));
            }

            if (eventCount < 64) {
                events[eventCount++] = e;
            }
        }

        // ── Update ──
        const Uint8* keys = SDL_GetKeyboardState(nullptr);
        SDL_SetRenderTarget(renderer, virtualScreen);
        game.update(events, eventCount, keys);

        // ── Draw to virtual screen ──
        game.draw();

        // ── Blit virtual screen to window ──
        SDL_SetRenderTarget(renderer, nullptr);
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
        SDL_RenderClear(renderer);

        SDL_Rect dstRect = {offsetX, offsetY, newW, newH};
        SDL_RenderCopy(renderer, virtualScreen, nullptr, &dstRect);
        SDL_RenderPresent(renderer);

        // ── Frame rate control ──
        Uint32 frameTime = SDL_GetTicks() - frameStart;
        if (frameTime < 1000 / TARGET_FPS) {
            SDL_Delay(1000 / TARGET_FPS - frameTime);
        }
    }

    // ── Cleanup ──
    SDL_DestroyTexture(virtualScreen);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    IMG_Quit();
    TTF_Quit();
    SDL_Quit();

    return 0;
}
