#pragma once
#include <random>
#include <cmath>
#include <algorithm>
#include <SDL.h>

inline std::mt19937& rng() {
    static std::mt19937 gen(std::random_device{}());
    return gen;
}

inline float randf(float lo, float hi) {
    return std::uniform_real_distribution<float>(lo, hi)(rng());
}
inline int randi(int lo, int hi) {
    return std::uniform_int_distribution<int>(lo, hi)(rng());
}
inline float randf01() { return randf(0.0f, 1.0f); }

inline float clamp(float v, float lo, float hi) {
    return std::max(lo, std::min(hi, v));
}
inline int clampi(int v, int lo, int hi) {
    return std::max(lo, std::min(hi, v));
}
inline float lerpf(float a, float b, float t) { return a + (b - a) * t; }

constexpr float PI = 3.14159265358979f;
constexpr float DEG2RAD = PI / 180.0f;
constexpr float RAD2DEG = 180.0f / PI;

struct Color {
    Uint8 r, g, b, a;
    Color() : r(255), g(255), b(255), a(255) {}
    Color(Uint8 r, Uint8 g, Uint8 b, Uint8 a = 255) : r(r), g(g), b(b), a(a) {}
    SDL_Color toSDL() const { return {r, g, b, a}; }
};

inline void SDL_SetRenderColor(SDL_Renderer* ren, const Color& c) {
    SDL_SetRenderDrawColor(ren, c.r, c.g, c.b, c.a);
}

inline void drawFilledCircle(SDL_Renderer* ren, int cx, int cy, int radius, const Color& col) {
    SDL_SetRenderDrawColor(ren, col.r, col.g, col.b, col.a);
    for (int dy = -radius; dy <= radius; dy++) {
        int dx = (int)std::sqrt(radius * radius - dy * dy);
        SDL_RenderDrawLine(ren, cx - dx, cy + dy, cx + dx, cy + dy);
    }
}

inline void drawRect(SDL_Renderer* ren, int x, int y, int w, int h, const Color& col) {
    SDL_SetRenderDrawColor(ren, col.r, col.g, col.b, col.a);
    SDL_Rect r = {x, y, w, h};
    SDL_RenderFillRect(ren, &r);
}
