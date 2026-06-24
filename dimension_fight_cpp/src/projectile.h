#pragma once
#include "vec2.h"
#include "utils.h"
#include "data.h"
#include <vector>

struct Projectile {
    Vec2 pos, vel;
    int damage;
    int size;
    Color color;
    Dimension dim;
    int life = 300;
    bool alive = true;
    bool piercing = false;

    Projectile() = default;
    Projectile(Vec2 p, Vec2 v, int dmg, int sz, Color c, Dimension d, bool pierce = false)
        : pos(p), vel(v), damage(dmg), size(sz), color(c), dim(d), piercing(pierce) {}

    void update() {
        pos += vel;
        life--;
        if (life <= 0) alive = false;
        // Out of bounds
        if (pos.x < -3000 || pos.x > 3000 || pos.y < -3000 || pos.y > 3000) alive = false;
    }

    void draw(SDL_Renderer* ren, Vec2 cam) const {
        if (!alive) return;
        int sx = (int)(pos.x - cam.x);
        int sy = (int)(pos.y - cam.y);
        if (sx < -50 || sx > SCREEN_W + 50 || sy < -50 || sy > SCREEN_H + 50) return;

        // Glow effect
        Color glow = color;
        glow.a = 80;
        drawFilledCircle(ren, sx, sy, size + 2, glow);
        drawFilledCircle(ren, sx, sy, size, color);
        // Core
        drawFilledCircle(ren, sx, sy, std::max(1, size / 2), Color(255,255,255,200));
    }
};

struct EnemyProjectile {
    Vec2 pos, vel;
    int damage = 1;
    int size = 4;
    Color color;
    Dimension dim;
    int life = 250;
    bool alive = true;

    EnemyProjectile() = default;
    EnemyProjectile(Vec2 p, Vec2 v, int dmg, Color c, Dimension d)
        : pos(p), vel(v), damage(dmg), color(c), dim(d) {}

    void update() {
        pos += vel;
        life--;
        if (life <= 0) alive = false;
        if (pos.x < -3000 || pos.x > 3000 || pos.y < -3000 || pos.y > 3000) alive = false;
    }

    void draw(SDL_Renderer* ren, Vec2 cam) const {
        if (!alive) return;
        int sx = (int)(pos.x - cam.x);
        int sy = (int)(pos.y - cam.y);
        if (sx < -50 || sx > SCREEN_W + 50 || sy < -50 || sy > SCREEN_H + 50) return;
        drawFilledCircle(ren, sx, sy, size, color);
    }
};

struct Gem {
    Vec2 pos;
    int xp;
    int size = 5;
    Color color;
    bool alive = true;
    int life = 600;
    float magnetRange = 120.0f;

    Gem() = default;
    Gem(Vec2 p, int xp, Color c = Color(100,200,255))
        : pos(p), xp(xp), color(c) {}

    void update(Vec2 playerPos) {
        life--;
        if (life <= 0) { alive = false; return; }
        // Magnet toward player
        float dist = pos.dist(playerPos);
        if (dist < magnetRange && dist > 1.0f) {
            Vec2 dir = (playerPos - pos).normalized();
            pos += dir * 3.5f;
        }
    }

    void draw(SDL_Renderer* ren, Vec2 cam) const {
        if (!alive) return;
        int sx = (int)(pos.x - cam.x);
        int sy = (int)(pos.y - cam.y);
        if (sx < -50 || sx > SCREEN_W + 50 || sy < -50 || sy > SCREEN_H + 50) return;
        // Diamond shape
        Color glow = color; glow.a = 100;
        drawFilledCircle(ren, sx, sy, size + 2, glow);
        drawFilledCircle(ren, sx, sy, size, color);
    }
};

struct PickupItem {
    Vec2 pos;
    ItemType type;
    Color color;
    bool alive = true;
    int life = 600;
    int size = 8;

    PickupItem() = default;
    PickupItem(Vec2 p, ItemType t, Color c) : pos(p), type(t), color(c) {}

    void update() {
        life--;
        if (life <= 0) alive = false;
    }

    void draw(SDL_Renderer* ren, Vec2 cam) const {
        if (!alive) return;
        int sx = (int)(pos.x - cam.x);
        int sy = (int)(pos.y - cam.y);
        if (sx < -50 || sx > SCREEN_W + 50 || sy < -50 || sy > SCREEN_H + 50) return;
        // Pulsing outline
        float pulse = 0.7f + 0.3f * std::sin(life * 0.1f);
        int r = (int)(size * pulse);
        Color glow = color; glow.a = 80;
        drawFilledCircle(ren, sx, sy, r + 3, glow);
        drawFilledCircle(ren, sx, sy, r, color);
        drawFilledCircle(ren, sx, sy, r / 2, Color(255,255,255,180));
    }
};
