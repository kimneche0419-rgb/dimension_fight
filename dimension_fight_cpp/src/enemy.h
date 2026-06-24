#pragma once
#include "vec2.h"
#include "utils.h"
#include "data.h"
#include "projectile.h"
#include <vector>
#include <string>

class Enemy {
public:
    Vec2 pos, vel;
    int typeIdx;
    std::string etype;
    int hp, maxHp;
    float speed;
    int size;
    int xpReward;
    int goldReward;
    Color color;
    Dimension dim;
    std::string behavior;
    int shootCD;
    int shootTimer = 0;
    bool alive = true;

    // Behavior state
    float zigzagAngle = 0;
    float orbitAngle = 0;
    int swarmSeed = 0;

    // Hit flash
    int hitFlash = 0;

    Enemy() = default;
    Enemy(int typeIndex, Vec2 spawnPos, float diffMult = 1.0f) : typeIdx(typeIndex) {
        auto& types = getEnemyTypes();
        auto& t = types[typeIndex];
        etype = t.key;
        pos = spawnPos;
        hp = (int)(t.hp * diffMult);
        maxHp = hp;
        speed = t.speed;
        size = t.size;
        xpReward = t.xp;
        goldReward = t.gold;
        color = t.color_p;
        dim = t.dim;
        behavior = t.behavior;
        shootCD = t.shoot_cd;
        zigzagAngle = randf(0, 360);
        orbitAngle = randf(0, 360);
        swarmSeed = randi(0, 1000);
    }

    std::vector<EnemyProjectile> update(Vec2 playerPos, Dimension playerDim) {
        std::vector<EnemyProjectile> bullets;
        if (!alive) return bullets;

        if (hitFlash > 0) hitFlash--;

        Vec2 toPlayer = playerPos - pos;
        float dist = toPlayer.length();
        Vec2 dir = dist > 1.0f ? toPlayer.normalized() : Vec2(0, 0);

        // Behavior
        if (behavior == "chase") {
            vel = dir * speed;
        } else if (behavior == "zigzag") {
            zigzagAngle += 3.0f;
            float zig = std::sin(zigzagAngle * DEG2RAD) * 2.0f;
            Vec2 perp(-dir.y, dir.x);
            vel = (dir + perp * zig * 0.3f).normalized() * speed;
        } else if (behavior == "swarm") {
            float wave = std::sin((swarmSeed + zigzagAngle) * DEG2RAD);
            zigzagAngle += 2.0f;
            Vec2 perp(-dir.y, dir.x);
            vel = (dir + perp * wave * 0.5f).normalized() * speed;
        } else if (behavior == "orbit") {
            if (dist > 200) {
                vel = dir * speed;
            } else {
                orbitAngle += 1.5f;
                Vec2 perp(-dir.y, dir.x);
                vel = perp * speed * 0.8f;
            }
        } else if (behavior == "boss") {
            if (dist > 150) {
                vel = dir * speed;
            } else {
                vel = vel * 0.95f;
            }
        }

        pos += vel;

        // Shooting
        if (shootCD > 0) {
            shootTimer++;
            if (shootTimer >= shootCD && dist < 600) {
                shootTimer = 0;
                Vec2 bulletDir = dir;
                float bulletSpeed = 5.0f;
                Color bulletCol(255, 100, 100);
                if (dim == Dimension::VOID_DIM) bulletCol = Color(200, 50, 255);

                if (behavior == "boss") {
                    // Boss fires spread
                    for (int i = -2; i <= 2; i++) {
                        float a = bulletDir.angle() + i * 15.0f * DEG2RAD;
                        Vec2 bv = Vec2::fromAngle(a, bulletSpeed);
                        bullets.emplace_back(pos, bv, 2, bulletCol, dim);
                    }
                } else {
                    Vec2 bv = bulletDir * bulletSpeed;
                    bullets.emplace_back(pos, bv, 1, bulletCol, dim);
                }
            }
        }

        return bullets;
    }

    void takeDamage(int dmg) {
        hp -= dmg;
        hitFlash = 6;
        if (hp <= 0) {
            hp = 0;
            alive = false;
        }
    }

    void draw(SDL_Renderer* ren, Vec2 cam) const {
        if (!alive) return;
        int sx = (int)(pos.x - cam.x);
        int sy = (int)(pos.y - cam.y);
        if (sx < -60 || sx > SCREEN_W + 60 || sy < -60 || sy > SCREEN_H + 60) return;

        Color drawCol = color;
        if (hitFlash > 0) {
            drawCol = Color(255, 255, 255);  // White flash
        }

        // Body
        drawFilledCircle(ren, sx, sy, size, drawCol);

        // Inner detail
        Color inner(drawCol.r / 2, drawCol.g / 2, drawCol.b / 2);
        drawFilledCircle(ren, sx, sy, size / 2, inner);

        // Eye/core
        drawFilledCircle(ren, sx, sy, 3, Color(255, 255, 255));

        // HP bar for tough enemies
        if (maxHp > 5 && hp < maxHp) {
            int barW = size * 2;
            int barH = 3;
            int bx = sx - barW / 2;
            int by = sy - size - 8;
            drawRect(ren, bx, by, barW, barH, Color(60, 60, 60));
            int fillW = (int)((float)barW * hp / maxHp);
            Color hpCol = (hp > maxHp / 2) ? Color(0,255,80) : Color(255,80,0);
            drawRect(ren, bx, by, fillW, barH, hpCol);
        }

        // Dimension indicator
        if (dim == Dimension::VOID_DIM) {
            Color ring(180, 0, 255, 80);
            drawFilledCircle(ren, sx, sy, size + 3, ring);
        }
    }
};
