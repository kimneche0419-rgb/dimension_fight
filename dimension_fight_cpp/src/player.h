#pragma once
#include "vec2.h"
#include "utils.h"
#include "data.h"
#include "projectile.h"
#include <vector>
#include <map>
#include <string>
#include <cmath>
#include <algorithm>

class Player {
public:
    Vec2 pos;
    Vec2 vel;
    float angle = 0;  // radians
    Dimension dim = Dimension::PHYSICAL;
    ShipMode mode = ShipMode::SHIP;

    // Stats
    int health = 100, maxHealth = 100;
    int shield = 30, maxShield = 30;
    int shieldRegenCD = 0;
    int level = 1;
    int xp = 0, xpToNext = 20;
    int score = 0;
    int gold = 0, diamonds = 0;
    int kills = 0;

    // Weapon
    int weaponIdx = 0;
    int shootCD = 0;
    float dmgMult = 1.0f;
    float fireRateMult = 1.0f;
    int multiShot = 0;
    float fruit_awaken_dmg_mult = 1.0f;
    float fruit_awaken_cd_mult = 1.0f;

    // Dash
    int dashTimer = 0;
    int dashCD = 0;
    Vec2 dashDir;
    bool dashing = false;

    // Ship color
    int colorIdx = 0;

    // Invincibility
    int iframes = 0;

    // Movement config
    float accel = 0.80f;
    float maxSpeed = 11.0f;
    float friction = 0.90f;
    float speedMult = 1.0f;
    float dashSpeed = 32.0f;
    int dashFrames = 12;
    int dashCooldown = 35;

    // Size
    int size = 16;

    // Alive
    bool alive = true;

    // ── 전직 시스템 및 플레이 통계 추적 ──
    struct JobStats {
        int melee_kills = 0;
        int range_kills = 0;
        int dash_count = 0;
        int skill_uses = 0;
        int damage_taken = 0;
        int weapon_switches = 0;
        int dim_switches = 0;
        int max_combo = 0;
        int vamp_kills = 0;
    } job_stats;

    std::string job = "";
    float _job_speed_mult = 1.0f;
    float _job_dmg_mult = 1.0f;
    float _job_cd_mult = 1.0f;
    float _job_skill_cd_mult = 1.0f;
    float _job_skill_dmg_mult = 1.0f;
    float _job_combo_bonus = 1.0f;
    int _job_lifesteal_bonus = 0;
    bool _job_double_dash = false;
    bool _job_void_immune = false;
    float _job_void_dmg_mult = 1.0f;
    float _job_gold_mult_bonus = 0.0f;
    float _job_potion_heal_bonus = 0.0f;

    // 더블 대쉬 관련 추가
    int extraDashes = 0;

    // ── 열매 및 스킬 ──
    std::string equipped_fruit = "";
    std::vector<std::string> active_skills;
    std::map<std::string, int> skill_cooldowns;
    bool skill_izanagi_ready = true;

    // ── 전설 제작 모듈 (Crafting Modules) ──
    bool craft_drone_laser = false;
    bool craft_time_barrier = false;
    bool craft_warp_engine = false;
    bool craft_fusion = false;
    bool craft_rift_gauntlet = false;
    bool craft_nanobot_pylon = false;
    bool craft_singularity_magnet = false;
    bool craft_photon_shield = false;
    bool craft_void_hyperdrive = false;
    bool craft_abyssal_orb = false;
    bool craft_void_crown = false;
    bool craft_time_chronograph = false;
    bool craft_multiverse_matrix = false;
    bool craft_nano_techpack = false;

    // ── 모듈 쿨타임 및 버프 타이머 ──
    int time_barrier_cd = 0;
    int time_barrier_timer = 0;
    int time_chrono_cd = 0;
    int void_crown_icd = 0;
    int matrix_speed_timer = 0;

    int skill_vamp_timer = 0;
    int skill_dmg_timer = 0;
    int skill_stealth_timer = 0;
    int skill_titan_timer = 0;
    int skill_gatling_timer = 0;

    // ── 콤보 ──
    int combo = 0;
    int combo_timer = 0;
    int max_combo = 0;

    Player() = default;
    Player(Vec2 startPos) : pos(startPos) {}

    void applyJob(const std::string& jkey, const JobData& jd, int masteryLvl = 0) {
        job = jkey;
        float boost = 1.0f + masteryLvl * 0.20f;
        _job_speed_mult = 1.0f + (jd.speed_mult - 1.0f) * boost;
        _job_dmg_mult = 1.0f + (jd.dmg_mult - 1.0f) * boost;
        _job_cd_mult = 1.0f + (jd.cd_mult - 1.0f) * boost;
        _job_skill_cd_mult = 1.0f + (jd.skill_cd_mult - 1.0f) * boost;
        _job_skill_dmg_mult = 1.0f + (jd.skill_dmg_mult - 1.0f) * boost;
        _job_combo_bonus = jd.combo_mult_bonus;
        _job_lifesteal_bonus = jd.lifesteal_bonus;
        _job_double_dash = jd.double_dash;
        _job_void_immune = jd.void_immune;
        _job_void_dmg_mult = jd.void_dmg_mult;
        _job_gold_mult_bonus = jd.gold_mult_bonus;
        _job_potion_heal_bonus = jd.potion_heal_bonus;

        int oldMaxHp = maxHealth;
        maxHealth = (int)(100.0f * jd.hp_mult);
        health = (health * maxHealth) / std::max(1, oldMaxHp);
        
        int oldMaxShield = maxShield;
        maxShield = (int)(30.0f * jd.shield_mult);
        shield = (maxShield > 0) ? (shield * maxShield) / std::max(1, oldMaxShield) : 0;
    }

    void resetJob() {
        job = "";
        _job_speed_mult = 1.0f;
        _job_dmg_mult = 1.0f;
        _job_cd_mult = 1.0f;
        _job_skill_cd_mult = 1.0f;
        _job_skill_dmg_mult = 1.0f;
        _job_combo_bonus = 1.0f;
        _job_lifesteal_bonus = 0;
        _job_double_dash = false;
        _job_void_immune = false;
        _job_void_dmg_mult = 1.0f;
        _job_gold_mult_bonus = 0.0f;
        _job_potion_heal_bonus = 0.0f;

        maxHealth = 100;
        if (health > maxHealth) health = maxHealth;
        maxShield = 30;
        if (shield > maxShield) shield = maxShield;
    }

    void update(const Uint8* keys, Vec2 mouseWorld) {
        if (!alive) return;

        if (iframes > 0) iframes--;

        // Cooldown and timers decrement
        for (auto& [skey, cd] : skill_cooldowns) {
            if (cd > 0) cd--;
        }
        if (time_barrier_cd > 0) time_barrier_cd--;
        if (time_barrier_timer > 0) time_barrier_timer--;
        if (time_chrono_cd > 0) time_chrono_cd--;
        if (void_crown_icd > 0) void_crown_icd--;
        if (matrix_speed_timer > 0) matrix_speed_timer--;

        if (skill_vamp_timer > 0) skill_vamp_timer--;
        if (skill_dmg_timer > 0) skill_dmg_timer--;
        if (skill_stealth_timer > 0) skill_stealth_timer--;
        if (skill_titan_timer > 0) skill_titan_timer--;
        if (skill_gatling_timer > 0) skill_gatling_timer--;

        if (combo_timer > 0) {
            combo_timer--;
            if (combo_timer <= 0) combo = 0;
        }

        // Dashing
        if (dashing) {
            vel = dashDir * dashSpeed;
            dashTimer--;
            if (dashTimer <= 0) {
                dashing = false;
                vel *= 0.3f;
                if (_job_double_dash && extraDashes > 0) {
                    // Double dash available
                } else {
                    extraDashes = 0;
                }
            }
        } else {
            // Movement
            Vec2 input(0, 0);
            if (keys[SDL_SCANCODE_W] || keys[SDL_SCANCODE_UP])    input.y -= 1;
            if (keys[SDL_SCANCODE_S] || keys[SDL_SCANCODE_DOWN])  input.y += 1;
            if (keys[SDL_SCANCODE_A] || keys[SDL_SCANCODE_LEFT])  input.x -= 1;
            if (keys[SDL_SCANCODE_D] || keys[SDL_SCANCODE_RIGHT]) input.x += 1;

            if (input.lengthSq() > 0) {
                input = input.normalized();
                vel += input * accel;
            }

            // Friction
            vel *= friction;

            // Speed cap calculation
            float currentSpeedMult = speedMult * _job_speed_mult;
            if (matrix_speed_timer > 0) currentSpeedMult *= 1.5f;
            if (skill_stealth_timer > 0) currentSpeedMult *= 1.4f;

            float spd = vel.length();
            float ms = maxSpeed * currentSpeedMult;
            if (spd > ms) vel = vel.normalized() * ms;
        }

        pos += vel;

        // World bounds
        pos.x = clamp(pos.x, -WORLD_SIZE/2, WORLD_SIZE/2);
        pos.y = clamp(pos.y, -WORLD_SIZE/2, WORLD_SIZE/2);

        // Aim angle
        Vec2 toMouse = mouseWorld - pos;
        if (toMouse.lengthSq() > 1.0f) {
            angle = toMouse.angle();
        }

        // Dash cooldown
        if (dashCD > 0) dashCD--;

        // Shoot cooldown
        if (shootCD > 0) shootCD--;

        // Shield regen (Abyssal Orb regeneration bonus)
        if (shieldRegenCD > 0) {
            shieldRegenCD--;
        } else if (shield < maxShield) {
            shield += craft_abyssal_orb ? 3 : 1;
            if (shield > maxShield) shield = maxShield;
            shieldRegenCD = 30;
        }
    }

    void dash() {
        if (dashing || dashCD > 0) {
            if (_job_double_dash && extraDashes == 0 && dashCD > 0) {
                extraDashes = 1;
                dashCD = 0; // Allow immediate double dash
            } else {
                return;
            }
        }
        dashing = true;
        dashTimer = dashFrames;
        
        int cd = dashCooldown;
        if (craft_warp_engine) cd /= 2;
        dashCD = (int)(cd * _job_cd_mult);

        dashDir = vel.lengthSq() > 0.1f ? vel.normalized() : Vec2::fromAngle(angle);
        
        int iframeCount = dashFrames;
        if (job == "시공돌격자") iframeCount += 10;
        if (craft_void_hyperdrive) iframeCount = std::max(iframeCount, 120);
        iframes = iframeCount;

        job_stats.dash_count++;
    }

    void shiftDimension() {
        if (_job_void_immune && dim == Dimension::PHYSICAL) {
            // Already immune, but perform standard shift
        }
        dim = (dim == Dimension::PHYSICAL) ? Dimension::VOID_DIM : Dimension::PHYSICAL;
        iframes = 15;
        job_stats.dim_switches++;
    }

    std::vector<Projectile> shoot(Vec2 targetWorld) {
        std::vector<Projectile> result;
        if (shootCD > 0) return result;

        auto& weapons = getWeapons();
        if (weaponIdx >= (int)weapons.size()) return result;
        auto& w = weapons[weaponIdx];

        float cd_m = 1.0f / fireRateMult * _job_cd_mult * fruit_awaken_cd_mult;
        if (health >= maxHealth && craft_void_hyperdrive) {
            cd_m *= 0.60f;
        }
        if (craft_multiverse_matrix) {
            cd_m *= 0.85f;
        }
        if (skill_gatling_timer > 0) {
            cd_m *= 0.30f; // Gatling skill shoot speed increase
        }
        shootCD = std::max(3, (int)(w.cooldown * cd_m));

        Color col = (dim == Dimension::PHYSICAL) ? w.color_p : w.color_v;

        Vec2 dir = (targetWorld - pos).normalized();
        int totalCount = w.count + multiShot;
        
        // Calculate dmg multiplier
        float currentDmgMult = dmgMult * _job_dmg_mult * fruit_awaken_dmg_mult;
        if (dim == Dimension::VOID_DIM) {
            currentDmgMult *= _job_void_dmg_mult;
            if (craft_void_crown) currentDmgMult *= 1.30f;
        }
        if (craft_multiverse_matrix) currentDmgMult *= 1.15f;
        if (skill_dmg_timer > 0) currentDmgMult *= 1.50f;
        int dmg = (int)(w.dmg * currentDmgMult);

        for (int i = 0; i < totalCount; i++) {
            float spreadAngle = 0;
            if (w.spread > 0) {
                spreadAngle = randf(-w.spread / 2.0f, w.spread / 2.0f) * DEG2RAD;
            }
            float baseAngle = dir.angle() + spreadAngle;
            Vec2 bulletVel = Vec2::fromAngle(baseAngle, w.speed);
            bool pierce = (std::string(w.key) == "sniper" || std::string(w.key) == "railgun");
            result.emplace_back(pos + dir * 20.0f, bulletVel, dmg, w.size, col, dim, pierce);
        }
        return result;
    }

    void takeDamage(int dmg) {
        if (iframes > 0 || dashing) return;

        // Photon Reflector module: 30% chance to reflect damage and trigger invincibility
        if (craft_photon_shield && randf01() < 0.30f) {
            iframes = 90;
            return;
        }

        if (shield > 0) {
            int absorbed = std::min(shield, dmg);
            shield -= absorbed;
            dmg -= absorbed;
        }
        if (dmg > 0) {
            health -= dmg;
            job_stats.damage_taken += dmg;
        }
        shieldRegenCD = 120;
        iframes = 20;

        // Time Barrier module: trigger invincibility if HP <= 30%
        if (craft_time_barrier && health > 0 && health <= maxHealth * 0.30f && time_barrier_cd <= 0) {
            time_barrier_timer = 180;
            time_barrier_cd = 7200;
            iframes = 180;
        }

        if (health <= 0) {
            // Time Chronograph module: prevent death once every 180 seconds
            if (craft_time_chronograph && time_chrono_cd <= 0) {
                health = maxHealth / 2;
                iframes = 180;
                time_chrono_cd = 10800;
                return;
            }
            health = 0;
            alive = false;
        }
    }

    void addXP(int amount) {
        xp += amount;
        while (xp >= xpToNext) {
            xp -= xpToNext;
            level++;
            xpToNext = (int)(xpToNext * 1.3f) + 5;
        }
    }

    int getMaxWeaponIdx() const {
        auto& weapons = getWeapons();
        int maxIdx = 0;
        for (int i = 0; i < (int)weapons.size(); i++) {
            if (level >= weapons[i].unlock_level) maxIdx = i;
        }
        return maxIdx;
    }

    void draw(SDL_Renderer* ren, Vec2 cam) const {
        if (!alive) return;
        int sx = (int)(pos.x - cam.x);
        int sy = (int)(pos.y - cam.y);

        if (iframes > 0 && (iframes / 3) % 2 == 0) return;

        auto& colors = getShipColors();
        Color body = colors[colorIdx % colors.size()].body;
        Color accent = colors[colorIdx % colors.size()].accent;

        if (dim == Dimension::VOID_DIM) {
            body = Color(body.r/2 + 128, body.g/3, body.b/2 + 128);
        }

        float cosA = std::cos(angle), sinA = std::sin(angle);

        int currentSize = size;
        if (skill_titan_timer > 0) currentSize = (int)(size * 1.8f);

        int x1 = sx + (int)(cosA * currentSize);
        int y1 = sy + (int)(sinA * currentSize);
        int x2 = sx + (int)(std::cos(angle + 2.5f) * currentSize * 0.7f);
        int y2 = sy + (int)(std::sin(angle + 2.5f) * currentSize * 0.7f);
        int x3 = sx + (int)(std::cos(angle - 2.5f) * currentSize * 0.7f);
        int y3 = sy + (int)(std::sin(angle - 2.5f) * currentSize * 0.7f);

        auto drawTriangle = [&](int ax, int ay, int bx, int by, int cx, int cy, Color c) {
            if (ay > by) { std::swap(ax,bx); std::swap(ay,by); }
            if (ay > cy) { std::swap(ax,cx); std::swap(ay,cy); }
            if (by > cy) { std::swap(bx,cx); std::swap(by,cy); }

            SDL_SetRenderDrawColor(ren, c.r, c.g, c.b, c.a);
            auto interp = [](int y, int y0, int x0, int y1, int x1) -> int {
                if (y1 == y0) return x0;
                return x0 + (x1 - x0) * (y - y0) / (y1 - y0);
            };
            for (int y = ay; y <= cy; y++) {
                int xStart, xEnd;
                if (y < by) {
                    xStart = interp(y, ay, ax, cy, cx);
                    xEnd   = interp(y, ay, ax, by, bx);
                } else {
                    xStart = interp(y, ay, ax, cy, cx);
                    xEnd   = interp(y, by, bx, cy, cx);
                }
                if (xStart > xEnd) std::swap(xStart, xEnd);
                SDL_RenderDrawLine(ren, xStart, y, xEnd, y);
            }
        };

        Vec2 enginePos = Vec2(sx, sy) - Vec2(cosA, sinA) * (float)currentSize * 0.6f;
        Color engineCol(255, 150, 50, 150);
        drawFilledCircle(ren, (int)enginePos.x, (int)enginePos.y, 5, engineCol);

        drawTriangle(x1, y1, x2, y2, x3, y3, body);

        drawFilledCircle(ren, sx + (int)(cosA * currentSize * 0.3f),
                         sy + (int)(sinA * currentSize * 0.3f), 3, accent);

        if (dim == Dimension::VOID_DIM) {
            Color ringCol(180, 0, 255, 100);
            drawFilledCircle(ren, sx, sy, currentSize + 4, ringCol);
        }

        if (dashing) {
            for (int i = 1; i <= 3; i++) {
                Vec2 tp = Vec2(sx, sy) - dashDir * (float)(i * 8);
                Color tc = body;
                tc.a = (Uint8)(150 / i);
                drawFilledCircle(ren, (int)tp.x, (int)tp.y, currentSize - i * 2, tc);
            }
        }
    }
};
