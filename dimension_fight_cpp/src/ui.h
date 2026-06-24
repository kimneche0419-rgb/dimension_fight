#pragma once
#include <SDL.h>
#include <SDL_ttf.h>
#include <string>
#include <map>
#include "utils.h"
#include "data.h"

class UI {
    std::map<int, TTF_Font*> fonts;
    SDL_Renderer* ren;
    std::string fontPath;

    TTF_Font* getFont(int size) {
        auto it = fonts.find(size);
        if (it != fonts.end()) return it->second;
        TTF_Font* f = TTF_OpenFont(fontPath.c_str(), size);
        if (!f) {
            SDL_Log("Failed to open font size %d: %s", size, TTF_GetError());
            // Try fallback
            f = TTF_OpenFont("C:\\Windows\\Fonts\\malgun.ttf", size);
        }
        if (f) fonts[size] = f;
        return f;
    }

public:
    UI() : ren(nullptr) {}

    ~UI() {
        for (auto& [k, v] : fonts) {
            if (v) TTF_CloseFont(v);
        }
    }

    bool init(SDL_Renderer* renderer, const std::string& fontFile) {
        ren = renderer;
        fontPath = fontFile;
        if (TTF_Init() < 0) {
            SDL_Log("TTF_Init failed: %s", TTF_GetError());
            return false;
        }
        // Pre-load common sizes
        getFont(14);
        getFont(18);
        getFont(24);
        getFont(36);
        getFont(48);
        return true;
    }

    void drawRectBorder(int x, int y, int w, int h, int thickness, Color col) {
        SDL_SetRenderDrawColor(ren, col.r, col.g, col.b, col.a);
        for (int i = 0; i < thickness; i++) {
            SDL_Rect r = { x + i, y + i, w - 2 * i, h - 2 * i };
            SDL_RenderDrawRect(ren, &r);
        }
    }

    void drawRectWithBorder(int x, int y, int w, int h, Color bg, Color border, int thickness = 1) {
        drawRect(ren, x, y, w, h, bg);
        drawRectBorder(x, y, w, h, thickness, border);
    }

    void setClipRect(int x, int y, int w, int h) {
        SDL_Rect r = { x, y, w, h };
        SDL_RenderSetClipRect(ren, &r);
    }

    void clearClipRect() {
        SDL_RenderSetClipRect(ren, nullptr);
    }

    void drawText(const std::string& text, int x, int y, int size,
                  Color col = Color(255,255,255), const std::string& align = "center") {
        TTF_Font* f = getFont(size);
        if (!f || text.empty()) return;

        SDL_Surface* surf = TTF_RenderUTF8_Blended(f, text.c_str(), col.toSDL());
        if (!surf) return;

        SDL_Texture* tex = SDL_CreateTextureFromSurface(ren, surf);
        if (!tex) { SDL_FreeSurface(surf); return; }

        SDL_Rect dst;
        dst.w = surf->w;
        dst.h = surf->h;

        if (align == "center") {
            dst.x = x - dst.w / 2;
            dst.y = y - dst.h / 2;
        } else if (align == "left") {
            dst.x = x;
            dst.y = y;
        } else { // right
            dst.x = x - dst.w;
            dst.y = y;
        }

        SDL_RenderCopy(ren, tex, nullptr, &dst);
        SDL_DestroyTexture(tex);
        SDL_FreeSurface(surf);
    }

    void drawTextWithBG(const std::string& text, int x, int y, int size,
                        Color col, Color bg) {
        TTF_Font* f = getFont(size);
        if (!f || text.empty()) return;

        int tw = 0, th = 0;
        TTF_SizeUTF8(f, text.c_str(), &tw, &th);
        drawRect(ren, x - tw/2 - 6, y - th/2 - 3, tw + 12, th + 6, bg);
        drawText(text, x, y, size, col, "center");
    }

    // ── HUD Drawing ──
    void drawHPBar(int hp, int maxHp, int shield, int maxShield) {
        int bx = 20, by = SCREEN_H - 35;
        int bw = 200, bh = 12;

        // HP background
        drawRect(ren, bx, by, bw, bh, Color(40, 0, 0));
        int hpW = (int)((float)bw * hp / std::max(1, maxHp));
        Color hpCol = (hp > maxHp / 3) ? Color(0, 220, 80) : Color(255, 60, 60);
        drawRect(ren, bx, by, hpW, bh, hpCol);

        // Shield bar above
        drawRect(ren, bx, by - 15, bw, 10, Color(0, 0, 40));
        int shW = (int)((float)bw * shield / std::max(1, maxShield));
        drawRect(ren, bx, by - 15, shW, 10, Color(80, 180, 255));

        // Text
        char buf[64];
        snprintf(buf, sizeof(buf), "HP %d/%d", hp, maxHp);
        drawText(buf, bx + bw / 2, by + bh / 2, 11, Color(255,255,255));
        snprintf(buf, sizeof(buf), "SH %d/%d", shield, maxShield);
        drawText(buf, bx + bw / 2, by - 10, 10, Color(200,220,255));
    }

    void drawXPBar(int xp, int xpToNext, int level) {
        int bx = 20, by = SCREEN_H - 52;
        int bw = 200, bh = 6;
        drawRect(ren, bx, by, bw, bh, Color(20, 20, 40));
        int xpW = (int)((float)bw * xp / std::max(1, xpToNext));
        drawRect(ren, bx, by, xpW, bh, Color(200, 100, 255));

        char buf[32];
        snprintf(buf, sizeof(buf), "Lv.%d", level);
        drawText(buf, bx - 2, by + 3, 12, Color(200, 180, 255), "right");
    }

    void drawWeaponInfo(int weaponIdx, int shootCD) {
        auto& weapons = getWeapons();
        if (weaponIdx >= (int)weapons.size()) return;
        auto& w = weapons[weaponIdx];

        int bx = SCREEN_W - 170, by = SCREEN_H - 80;
        int bw = 150, bh = 60;

        // Draw weapon box (container)
        drawRectWithBorder(bx, by, bw, bh, Color(10, 15, 30, 200), Color(0, 180, 255, 120), 1);

        // Weapon name
        drawText(w.name, bx + bw / 2, by + 18, 12, Color(255, 230, 100), "center");

        // Stats short info
        char statsBuf[64];
        snprintf(statsBuf, sizeof(statsBuf), "DMG: %d  SPD: %.1f", w.dmg, w.speed);
        drawText(statsBuf, bx + bw / 2, by + 36, 9, Color(160, 180, 200), "center");

        // Switch Hint
        drawText("Q/E: Switch Weapon", bx + bw / 2, by + 50, 8, Color(100, 120, 150), "center");

        // Cooldown flash/indicator
        if (shootCD > 0) {
            drawRect(ren, bx + 2, by + bh - 4, bw - 4, 2, Color(255, 100, 100));
        } else {
            drawRect(ren, bx + 2, by + bh - 4, bw - 4, 2, Color(80, 255, 80));
        }
    }

    void drawScore(int score, int gold, int diamonds) {
        char buf[64];
        snprintf(buf, sizeof(buf), "SCORE: %d", score);
        drawText(buf, SCREEN_W / 2, 15, 16, Color(255, 200, 50));

        snprintf(buf, sizeof(buf), "G: %d  D: %d", gold, diamonds);
        drawText(buf, SCREEN_W / 2, 35, 12, Color(255, 215, 0));
    }

    void drawNotify(const std::string& text, float alpha) {
        if (text.empty() || alpha <= 0) return;
        Color c(255, 255, 200, (Uint8)(alpha * 255));
        Color bg(0, 0, 0, (Uint8)(alpha * 150));
        drawTextWithBG(text, SCREEN_W / 2, 80, 16, c, bg);
    }

    void drawDimensionIndicator(Dimension dim) {
        const char* dimText = (dim == Dimension::PHYSICAL) ? "PHYSICAL" : "VOID";
        Color dimCol = (dim == Dimension::PHYSICAL) ? Color(100, 200, 255) : Color(200, 80, 255);
        drawText(dimText, SCREEN_W - 60, 20, 14, dimCol);
    }

    void drawDashIndicator(int dashCD) {
        Color col = (dashCD <= 0) ? Color(80, 255, 80) : Color(100, 100, 100);
        const char* text = (dashCD <= 0) ? "DASH [SPACE]" : "DASH ...";
        drawText(text, 20, SCREEN_H - 65, 11, col, "left");
    }

    void drawMinimap(Vec2 playerPos, const std::vector<Vec2>& enemyPositions,
                     Dimension playerDim) {
        int mx = SCREEN_W - 90, my = 50;
        int mw = 80, mh = 80;
        float scale = mw / WORLD_SIZE;

        // Background
        drawRect(ren, mx, my, mw, mh, Color(0, 0, 0, 150));
        // Border
        SDL_SetRenderDrawColor(ren, 100, 100, 150, 200);
        SDL_Rect border = {mx, my, mw, mh};
        SDL_RenderDrawRect(ren, &border);

        // Player dot
        int px = mx + mw / 2 + (int)(playerPos.x * scale);
        int py = my + mh / 2 + (int)(playerPos.y * scale);
        drawFilledCircle(ren, clampi(px, mx, mx + mw), clampi(py, my, my + mh), 2, Color(0, 255, 100));

        // Enemy dots
        for (auto& ep : enemyPositions) {
            int ex = mx + mw / 2 + (int)(ep.x * scale);
            int ey = my + mh / 2 + (int)(ep.y * scale);
            if (ex >= mx && ex <= mx + mw && ey >= my && ey <= my + mh) {
                drawFilledCircle(ren, ex, ey, 1, Color(255, 80, 80));
            }
        }
    }

    void drawFPS(int fps) {
        char buf[16];
        snprintf(buf, sizeof(buf), "FPS: %d", fps);
        drawText(buf, 60, 12, 11, Color(100, 100, 100), "left");
    }

    void drawSkillSlotBar(const std::vector<std::string>& active_skills, std::map<std::string, int>& skill_cooldowns) {
        int slot_w = 60, slot_h = 56;
        int gap = 8;
        int total_h = slot_h * 6 + gap * 5;
        int bar_x = 12;
        int bar_y = 70;

        // Draw side bar background (semi-transparent glassmorphism)
        Color bgCol(10, 15, 30, 180);
        Color borderCol(0, 180, 255, 100);
        drawRectWithBorder(bar_x - 8, bar_y - 8, slot_w + 16, total_h + 16, bgCol, borderCol, 1);

        auto& skillsDB = getAnimeSkills();

        for (int i = 0; i < 6; i++) {
            int sx = bar_x;
            int sy = bar_y + i * (slot_h + gap);

            if (i < (int)active_skills.size()) {
                std::string skey = active_skills[i];
                auto sIt = skillsDB.find(skey);
                if (sIt != skillsDB.end()) {
                    auto& sdata = sIt->second;
                    auto cdIt = skill_cooldowns.find(skey);
                    int cd = (cdIt != skill_cooldowns.end()) ? cdIt->second : 0;
                    int max_cd = sdata.cd;

                    // Box background (reddish if on cooldown, blue/dark if ready)
                    Color boxBg = (cd > 0) ? Color(45, 20, 15, 200) : Color(20, 35, 65, 200);
                    Color boxBorder = (cd == 0) ? Color(255, 215, 0) : Color(120, 60, 40);

                    drawRectWithBorder(sx, sy, slot_w, slot_h, boxBg, boxBorder, 1);

                    // Cooldown overlay (bottom to top fill)
                    if (cd > 0 && max_cd > 0) {
                        float cd_ratio = (float)cd / max_cd;
                        int fill_h = (int)(slot_h * cd_ratio);
                        drawRect(ren, sx, sy + slot_h - fill_h, slot_w, fill_h, Color(100, 30, 20, 160));
                    }

                    // Key index (top-left)
                    char numBuf[4];
                    snprintf(numBuf, sizeof(numBuf), "%d", i + 1);
                    drawText(numBuf, sx + 8, sy + 10, 10, Color(255, 255, 120), "center");

                    // Skill circle icon (center)
                    drawFilledCircle(ren, sx + slot_w / 2, sy + 22, 8, sdata.color);
                    drawFilledCircle(ren, sx + slot_w / 2, sy + 22, 6, Color(255, 255, 255, 120));

                    // Skill Name abbreviated (bottom)
                    std::string shortName = sdata.name;
                    if (shortName.size() > 8) shortName = shortName.substr(0, 8); // Simple truncation for rendering space
                    drawText(shortName, sx + slot_w / 2, sy + 44, 9, Color(230, 230, 230), "center");

                    // Cooldown value text
                    if (cd > 0) {
                        char cdBuf[16];
                        snprintf(cdBuf, sizeof(cdBuf), "%.1fs", cd / 60.0f);
                        drawText(cdBuf, sx + slot_w / 2, sy + 24, 11, Color(255, 255, 255), "center");
                    }
                }
            } else {
                // Empty slot
                drawRectWithBorder(sx, sy, slot_w, slot_h, Color(15, 15, 25, 200), Color(50, 50, 70), 1);
                char numBuf[4];
                snprintf(numBuf, sizeof(numBuf), "%d", i + 1);
                drawText(numBuf, sx + 8, sy + 10, 10, Color(60, 60, 80), "center");
            }
        }
    }
};
