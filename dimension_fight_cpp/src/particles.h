#pragma once
#include "vec2.h"
#include "utils.h"
#include <vector>

struct Particle {
    Vec2 pos, vel;
    Color col;
    int life, maxLife;
    int size;
    bool alive = true;

    Particle() = default;
    Particle(Vec2 p, Vec2 v, Color c, int life, int sz)
        : pos(p), vel(v), col(c), life(life), maxLife(life), size(sz) {}

    void update() {
        pos += vel;
        vel *= 0.97f;
        life--;
        if (life <= 0) alive = false;
    }

    void draw(SDL_Renderer* ren, Vec2 cam) const {
        if (!alive) return;
        float alpha = (float)life / (float)maxLife;
        int sx = (int)(pos.x - cam.x);
        int sy = (int)(pos.y - cam.y);
        if (sx < -20 || sx > SCREEN_W + 20 || sy < -20 || sy > SCREEN_H + 20) return;
        Color c = col;
        c.a = (Uint8)(alpha * 255);
        drawFilledCircle(ren, sx, sy, std::max(1, (int)(size * alpha)), c);
    }
};

class ParticleSystem {
public:
    std::vector<Particle> particles;

    void burst(Vec2 pos, Color col, int count = 12, float speed = 4.0f, int life = 30) {
        for (int i = 0; i < count; i++) {
            float a = randf(0, 360) * DEG2RAD;
            float spd = randf(1.0f, speed);
            Vec2 vel = Vec2::fromAngle(a, spd);
            int sz = randi(2, 5);
            particles.emplace_back(pos, vel, col, life + randi(-5, 5), sz);
        }
    }

    void update() {
        for (auto& p : particles) p.update();
        particles.erase(
            std::remove_if(particles.begin(), particles.end(),
                [](const Particle& p) { return !p.alive; }),
            particles.end());
    }

    void draw(SDL_Renderer* ren, Vec2 cam) const {
        for (const auto& p : particles) p.draw(ren, cam);
    }

    void clear() { particles.clear(); }
};
