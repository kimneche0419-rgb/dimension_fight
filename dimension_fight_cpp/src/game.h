#pragma once
#include <SDL.h>
#include <vector>
#include <string>
#include <algorithm>
#include <cmath>
#include "vec2.h"
#include "utils.h"
#include "data.h"
#include "player.h"
#include "enemy.h"
#include "projectile.h"
#include "particles.h"
#include "camera.h"
#include "starfield.h"
#include "sound.h"
#include "save.h"
#include "ui.h"
#include "network.h"

class Game {
public:
    SDL_Renderer* ren;
    UI ui;
    SoundManager sound;
    Camera camera;
    StarField starField;
    ParticleSystem particles;
    SaveData saveData;

    // ── Multiplayer Stats ──
    NetworkClient netClient;
    std::string mpStatus = "";
    int lobbyInputSel = 0;
    std::string userTyped = "";
    std::string passTyped = "";
    std::string serverIP = "127.0.0.1";
    bool mpSearching = false;
    float mpSearchTimer = 0.0f;
    bool isMultiplayer = false;
    std::string mpRole = "";
    std::string mpMode = "";
    std::string peerName = "";
    Vec2 peerPos;
    float peerAngle = 0.0f;
    int peerHP = 100, peerMaxHP = 100;
    int peerShield = 30, peerMaxShield = 30;
    int peerWeaponIdx = 0;
    Dimension peerDim = Dimension::PHYSICAL;
    bool peerActive = false;
    int peerScore = 0;
    std::string mpShootInfo = "";

    // State
    GameState state = GameState::MENU;
    Dimension dimension = Dimension::PHYSICAL;

    // Entities
    Player player;
    std::vector<Enemy> enemies;
    std::vector<Projectile> projectiles;
    std::vector<EnemyProjectile> enemyProjectiles;
    std::vector<Gem> gems;
    std::vector<PickupItem> items;

    // Game session
    int gameTime = 0;
    int spawnTimer = 0;
    float difficulty = 1.0f;
    int chapterIdx = 0;

    // Menu
    int menuSel = 0;
    int menuAnimTimer = 0;
    int colorSelectIdx = 0;

    // Levelup
    bool levelupActive = false;
    struct LevelupOption { LevelupType type; std::string name; std::string desc; };
    std::vector<LevelupOption> levelupChoices;
    int levelupSel = 0;
    int pendingLevelups = 0;

    // ── Shop System ──
    int shopSel = 0;
    int shopScrollY = 0;
    bool skillManageOpen = false;
    int skillManageSel = 0;

    // ── Gacha System ──
    int gachaClickCD = 0;
    std::string gachaTab = "뽑기";
    std::string gachaSeriesFilter = "전체";
    int gachaScrollY = 0;
    int gachaAnimTimer = 0;
    std::vector<std::string> gachaResults;
    int gachaRevealIdx = 0;

    // ── Crafting System ──
    int craftScrollY = 0;

    // ── Job Shop ──
    int jobShopSel = 0;

    // ── Ship Shop ──
    int shipShopSel = 0;

    // ── Job Select Overlay ──
    bool jobSelectActive = false;
    int jobSelectTimer = 0;
    std::vector<std::string> jobSelectChoices;
    bool jobSelectedThisChapter = false;

    // Notification
    std::string notifyText;
    int notifyTimer = 0;

    // Score / Economy
    int totalGold = 0;
    int totalDiamonds = 0;

    // FPS
    int fps = 0;
    int frameCount = 0;
    Uint32 fpsTimer = 0;

    // Item drop timer
    int itemTimer = 0;

    // Mouse
    Vec2 mouseScreen;
    Vec2 mouseWorld;

    bool init(SDL_Renderer* renderer) {
        ren = renderer;

        // Init UI with system Korean font
        if (!ui.init(renderer, "C:\\Windows\\Fonts\\malgun.ttf")) {
            SDL_Log("UI init failed, trying bundled font...");
            ui.init(renderer, "assets/fonts/NanumGothic.ttf");
        }

        // Init sound
        sound.init();

        // Load save
        saveData.load();
        totalGold = saveData.gold;
        totalDiamonds = saveData.diamonds;

        // Auto-login if session exists
        std::string savedUser, savedPass;
        if (netClient.loadSession(savedUser, savedPass)) {
            SDL_Log("Found active login session. Attempting auto-login for user: %s", savedUser.c_str());
            if (netClient.loginUser(savedUser, savedPass, saveData, serverIP)) {
                totalGold = saveData.gold;
                totalDiamonds = saveData.diamonds;
                SDL_Log("Auto-login on startup succeeded!");
            } else {
                SDL_Log("Auto-login on startup failed.");
            }
        }

        fpsTimer = SDL_GetTicks();
        return true;
    }

    void notify(const std::string& text, int duration = 120) {
        notifyText = text;
        notifyTimer = duration;
    }

    // ── Start Game ──
    void startGame(int chapIdx) {
        chapterIdx = chapIdx;
        auto& chapters = getChapters();
        auto& ch = chapters[chapterIdx % chapters.size()];

        player = Player(Vec2(0, 0));
        player.mode = ch.mode;
        player.colorIdx = colorSelectIdx;
        player.dim = Dimension::PHYSICAL;

        // Apply permanent upgrades
        player.maxShield += saveData.upgrades[0] * 5;
        player.shield = player.maxShield;
        player.speedMult = 1.0f + saveData.upgrades[1] * 0.03f;
        player.maxHealth += saveData.upgrades[2] * 10;
        player.health = player.maxHealth;
        player.dmgMult = 1.0f + saveData.upgrades[5] * 0.10f;

        // Apply equipped ship bonuses
        {
            auto& ships = getShipTypes();
            for (auto& s : ships) {
                if (std::string(s.key) == saveData.equipped_ship) {
                    auto it = saveData.ship_levels.find(s.key);
                    int lvl = (it != saveData.ship_levels.end()) ? it->second : 0;
                    if (lvl > 0) {
                        player.maxHealth  += s.hp_per_lvl * lvl;
                        player.maxShield  += s.shield_per_lvl * lvl;
                        player.health      = player.maxHealth;
                        player.shield      = player.maxShield;
                        player.dmgMult    *= (1.0f + s.dmg_pct_per_lvl * lvl * 0.01f);
                        player.speedMult  *= (1.0f + s.speed_pct_per_lvl * lvl * 0.01f);
                    }
                    break;
                }
            }
        }

        enemies.clear();
        projectiles.clear();
        enemyProjectiles.clear();
        gems.clear();
        items.clear();
        particles.clear();
        camera.offset = Vec2(-SCREEN_W / 2.0f, -SCREEN_H / 2.0f);

        gameTime = 0;
        spawnTimer = 0;
        difficulty = 1.0f;
        levelupActive = false;
        pendingLevelups = 0;
        itemTimer = 0;

        // Apply active job and mastery
        if (!saveData.player_job.empty()) {
            auto it = getJobData().find(saveData.player_job);
            if (it != getJobData().end()) {
                int mastery = 0;
                auto mIt = saveData.job_upgrades.find(saveData.player_job);
                if (mIt != saveData.job_upgrades.end()) mastery = mIt->second;
                player.applyJob(saveData.player_job, it->second, mastery);
            }
        }

        // Apply active fruit & skills
        player.equipped_fruit = saveData.equipped_fruit;
        player.active_skills = saveData.equipped_skills;

        // Apply fruit awakening boosts
        applyFruitAwakeningBoosts();

        // Apply crafted modules
        applyCraftedModules();

        // Reset Job Select variables
        jobSelectActive = false;
        jobSelectTimer = 0;
        jobSelectedThisChapter = false;

        dimension = Dimension::PHYSICAL;
        state = GameState::PLAYING;
        notify("WASD Move  SPACE Dash  SHIFT Dimension  Q/E Weapon", 220);
    }

    // ── Update ──
    void update(const SDL_Event* events, int eventCount, const Uint8* keys) {
        menuAnimTimer++;

        // FPS counter
        frameCount++;
        Uint32 now = SDL_GetTicks();
        if (now - fpsTimer >= 1000) {
            fps = frameCount;
            frameCount = 0;
            fpsTimer = now;
        }

        // Notification timer
        if (notifyTimer > 0) notifyTimer--;

        // Process events
        for (int i = 0; i < eventCount; i++) {
            auto& e = events[i];
            handleEvent(e, keys);
        }

        if (state == GameState::PLAYING && !levelupActive && !jobSelectActive) {
            updatePlaying(keys);
        }

        if (state == GameState::MULTIPLAYER_LOBBY && mpSearching) {
            mpSearchTimer += 1.0f;
            std::string role, peerIP, peerNameStr;
            int peerPort = 9001;
            if (netClient.pollMatchResult(role, peerIP, peerPort, peerNameStr)) {
                mpSearching = false;
                peerName = peerNameStr;
                mpRole = role;
                isMultiplayer = true;
                peerActive = false;
                SDL_StopTextInput();

                if (role == "HOST") {
                    mpStatus = "릴레이 서버 연결 중 (HOST)...";
                    if (netClient.relayConnect(peerIP, peerPort, netClient.currentSessionId, "HOST", netClient.loggedUser)) {
                        startGame(1);
                        state = GameState::PLAYING;
                        notify("⚔️ 멀티플레이가 시작되었습니다! HOST", 150);
                    } else {
                        mpStatus = "❌ 릴레이 서버 연결 실패";
                        isMultiplayer = false;
                    }
                } else {
                    mpStatus = "릴레이 서버 연결 중 (CLIENT)...";
                    Sleep(500);
                    if (netClient.relayConnect(peerIP, peerPort, netClient.currentSessionId, "CLIENT", netClient.loggedUser)) {
                        startGame(1);
                        state = GameState::PLAYING;
                        notify("⚔️ 멀티플레이가 시작되었습니다! CLIENT", 150);
                    } else {
                        mpStatus = "❌ 릴레이 서버 연결 실패";
                        isMultiplayer = false;
                    }
                }
            }
        }

        // BGM
        std::string stateStr;
        switch (state) {
            case GameState::MENU: stateStr = "MENU"; break;
            case GameState::PLAYING: stateStr = "PLAYING"; break;
            case GameState::DEATH: stateStr = "DEATH"; break;
            case GameState::WIN: stateStr = "WIN"; break;
            case GameState::SHOP: stateStr = "SHOP"; break;
            case GameState::GACHA: stateStr = "GACHA"; break;
            case GameState::CRAFTING: stateStr = "CRAFTING"; break;
            case GameState::JOB_SHOP: stateStr = "JOB_SHOP"; break;
            case GameState::SHIP_SHOP: stateStr = "SHIP_SHOP"; break;
            default: stateStr = "MENU"; break;
        }
        bool hasBoss = false;
        for (auto& e : enemies) if (e.behavior == "boss" && e.alive) hasBoss = true;
        sound.updateBGM(stateStr, hasBoss);
    }

    void handleEvent(const SDL_Event& e, const Uint8* keys) {
        if (e.type == SDL_MOUSEMOTION) {
            mouseScreen = Vec2((float)e.motion.x, (float)e.motion.y);
            mouseWorld = mouseScreen + camera.offset;
        }
        if (e.type == SDL_MOUSEBUTTONDOWN) {
            mouseScreen = Vec2((float)e.button.x, (float)e.button.y);
            mouseWorld = mouseScreen + camera.offset;
        }

        switch (state) {
            case GameState::MENU: handleMenuEvent(e); break;
            case GameState::COLOR_SELECT: handleColorSelectEvent(e); break;
            case GameState::PLAYING: handlePlayingEvent(e, keys); break;
            case GameState::SHOP: handleShopEvent(e); break;
            case GameState::GACHA: handleGachaEvent(e); break;
            case GameState::CRAFTING: handleCraftingEvent(e); break;
            case GameState::JOB_SHOP: handleJobShopEvent(e); break;
            case GameState::SHIP_SHOP: handleShipShopEvent(e); break;
            case GameState::MULTIPLAYER_LOBBY: handleMultiplayerLobbyEvent(e); break;
            case GameState::DEATH:
            case GameState::WIN:
                if (e.type == SDL_KEYDOWN && e.key.keysym.scancode == SDL_SCANCODE_R) {
                    // Return to menu + save
                    grantDeathRewards();
                    state = GameState::MENU;
                }
                break;
            default: break;
        }
    }

    void handleMenuEvent(const SDL_Event& e) {
        auto& chapters = getChapters();
        int numChapters = (int)chapters.size();

        if (e.type == SDL_KEYDOWN) {
            switch (e.key.keysym.scancode) {
                case SDL_SCANCODE_UP:
                    menuSel = (menuSel - 1 + numChapters) % numChapters; break;
                case SDL_SCANCODE_DOWN:
                    menuSel = (menuSel + 1) % numChapters; break;
                case SDL_SCANCODE_RETURN: case SDL_SCANCODE_SPACE:
                    if (menuSel > saveData.max_unlocked_chapter - 1) {
                        sound.playSFX("hit");
                        notify("🔒 이전 챕터를 먼저 클리어하세요!", 120);
                    } else {
                        state = GameState::COLOR_SELECT;
                        colorSelectIdx = 0;
                    }
                    break;
                case SDL_SCANCODE_S:
                    state = GameState::SHOP;
                    shopSel = 0;
                    shopScrollY = 0;
                    break;
                case SDL_SCANCODE_C:
                    state = GameState::CRAFTING;
                    craftScrollY = 0;
                    break;
                case SDL_SCANCODE_J:
                    state = GameState::JOB_SHOP;
                    jobShopSel = 0;
                    break;
                case SDL_SCANCODE_G:
                    state = GameState::GACHA;
                    gachaTab = "뽑기";
                    gachaScrollY = 0;
                    break;
                case SDL_SCANCODE_V:
                    state = GameState::SHIP_SHOP;
                    shipShopSel = 0;
                    break;
                case SDL_SCANCODE_M:
                    state = GameState::MULTIPLAYER_LOBBY;
                    mpStatus = "서버 연결 대기 중...";
                    SDL_StopTextInput();
                    {
                        std::string savedUser, savedPass;
                        if (netClient.loadSession(savedUser, savedPass)) {
                            mpStatus = "자동 로그인 중 (Auto-logging in)...";
                            if (netClient.loginUser(savedUser, savedPass, saveData, serverIP)) {
                                mpStatus = "자동 로그인 성공!";
                                totalGold = saveData.gold;
                                totalDiamonds = saveData.diamonds;
                            } else {
                                mpStatus = "자동 로그인 실패. 직접 로그인해 주세요.";
                                SDL_StartTextInput();
                            }
                        } else {
                            SDL_StartTextInput();
                        }
                    }
                    break;
                default: break;
            }
        }
        if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
            // Check chapter buttons
            for (int i = 0; i < numChapters; i++) {
                int by = 200 + i * 55;
                if (mouseScreen.x >= 200 && mouseScreen.x <= 600 &&
                    mouseScreen.y >= by && mouseScreen.y <= by + 45) {
                    menuSel = i;
                    if (i > saveData.max_unlocked_chapter - 1) {
                        sound.playSFX("hit");
                        notify("🔒 이전 챕터를 먼저 클리어하세요!", 120);
                    } else {
                        state = GameState::COLOR_SELECT;
                        colorSelectIdx = 0;
                    }
                }
            }
        }
    }

    void handleColorSelectEvent(const SDL_Event& e) {
        auto& colors = getShipColors();
        int numColors = (int)colors.size();
        if (e.type == SDL_KEYDOWN) {
            switch (e.key.keysym.scancode) {
                case SDL_SCANCODE_LEFT: case SDL_SCANCODE_A:
                    colorSelectIdx = (colorSelectIdx - 1 + numColors) % numColors; break;
                case SDL_SCANCODE_RIGHT: case SDL_SCANCODE_D:
                    colorSelectIdx = (colorSelectIdx + 1) % numColors; break;
                case SDL_SCANCODE_RETURN: case SDL_SCANCODE_SPACE:
                    startGame(menuSel); break;
                case SDL_SCANCODE_ESCAPE:
                    state = GameState::MENU; break;
                default: break;
            }
        }
    }

    void handlePlayingEvent(const SDL_Event& e, const Uint8* keys) {
        if (jobSelectActive) {
            handleJobSelectEvent(e);
            return;
        }

        if (levelupActive) {
            if (e.type == SDL_KEYDOWN) {
                switch (e.key.keysym.scancode) {
                    case SDL_SCANCODE_UP: case SDL_SCANCODE_W:
                        levelupSel = (levelupSel - 1 + (int)levelupChoices.size()) %
                                     (int)levelupChoices.size();
                        break;
                    case SDL_SCANCODE_DOWN: case SDL_SCANCODE_S:
                        levelupSel = (levelupSel + 1) % (int)levelupChoices.size();
                        break;
                    case SDL_SCANCODE_RETURN: case SDL_SCANCODE_SPACE:
                        applyLevelupChoice(levelupSel);
                        break;
                    default: break;
                }
            }
            if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
                for (int i = 0; i < (int)levelupChoices.size(); i++) {
                    int by = 220 + i * 70;
                    if (mouseScreen.x >= 200 && mouseScreen.x <= 600 &&
                        mouseScreen.y >= by && mouseScreen.y <= by + 60) {
                        applyLevelupChoice(i);
                    }
                }
            }
            return;
        }

        if (e.type == SDL_KEYDOWN) {
            switch (e.key.keysym.scancode) {
                case SDL_SCANCODE_SPACE:
                    player.dash();
                    break;
                case SDL_SCANCODE_ESCAPE:
                    state = GameState::MENU;
                    saveData.save();
                    notify("Lobby로 돌아왔습니다. 진행 상황 저장됨.", 120);
                    break;
                case SDL_SCANCODE_1: useSkill(0); break;
                case SDL_SCANCODE_2: useSkill(1); break;
                case SDL_SCANCODE_3: useSkill(2); break;
                case SDL_SCANCODE_4: useSkill(3); break;
                case SDL_SCANCODE_5: useSkill(4); break;
                case SDL_SCANCODE_6: useSkill(5); break;
                case SDL_SCANCODE_LSHIFT: case SDL_SCANCODE_RSHIFT:
                    player.shiftDimension();
                    dimension = player.dim;
                    sound.playSFX("shift");
                    particles.burst(player.pos, Color(180, 80, 255), 20, 6.0f, 25);
                    break;
                case SDL_SCANCODE_Q: {
                    int maxW = player.getMaxWeaponIdx();
                    player.weaponIdx = (player.weaponIdx - 1 + maxW + 1) % (maxW + 1);
                    auto& w = getWeapons()[player.weaponIdx];
                    notify(std::string("Weapon: ") + w.name, 60);
                    break;
                }
                case SDL_SCANCODE_E: {
                    int maxW = player.getMaxWeaponIdx();
                    player.weaponIdx = (player.weaponIdx + 1) % (maxW + 1);
                    auto& w = getWeapons()[player.weaponIdx];
                    notify(std::string("Weapon: ") + w.name, 60);
                    break;
                }
                case SDL_SCANCODE_R: {
                    if (totalGold >= 3000) {
                        totalGold -= 3000;
                        saveData.gold = totalGold;
                        triggerJobSelect();
                        notify("💎 3000 골드를 지불하여 다시 전직합니다!", 150);
                        saveData.save();
                    } else if (totalDiamonds >= 30) {
                        totalDiamonds -= 30;
                        saveData.diamonds = totalDiamonds;
                        triggerJobSelect();
                        notify("💎 30 다이아몬드를 지불하여 다시 전직합니다!", 150);
                        saveData.save();
                    } else {
                        notify("재전직 비용이 부족합니다! (3000 골드 또는 30 다이아몬드 필요)", 120);
                    }
                    break;
                }
                default: break;
            }
        }

        // Manual shoot on click
        if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
            auto bullets = player.shoot(mouseWorld);
            for (auto& b : bullets) projectiles.push_back(b);
            if (!bullets.empty()) {
                sound.playSFX("shoot");
                if (isMultiplayer && !bullets.empty()) {
                    auto& b = bullets[0];
                    char sBuf[256];
                    snprintf(sBuf, sizeof(sBuf), "SHOOT %.2f %.2f %.2f %.2f %d %d %d %d %d %d",
                             b.pos.x, b.pos.y, b.vel.x, b.vel.y, b.damage, b.size, b.color.r, b.color.g, b.color.b, (int)b.dim);
                    mpShootInfo = sBuf;
                }
            }
        }
    }

    void updatePlaying(const Uint8* keys) {
        if (isMultiplayer && netClient.peerSock != INVALID_SOCKET) {
            // Send state
            char stateBuf[512];
            snprintf(stateBuf, sizeof(stateBuf), "MYSTATE %.2f %.2f %.2f %d %d %d %d %d",
                     player.pos.x, player.pos.y, player.angle, player.health, player.shield, player.weaponIdx, (int)player.dim, player.score);
            std::string stateLine = stateBuf;

            if (!mpShootInfo.empty()) {
                stateLine += " " + mpShootInfo;
                mpShootInfo = "";
            }
            netClient.sendLine(netClient.peerSock, stateLine);

            // Read peer state
            while (true) {
                std::string line = netClient.recvLine(netClient.peerSock, false);
                if (line == "__WOULD_BLOCK__") break;
                if (line == "__CLOSED__" || line == "__ERROR__") {
                    notify("⚠️ 멀티플레이어 연결이 끊어졌습니다!", 120);
                    isMultiplayer = false;
                    netClient.cleanup();
                    state = GameState::MENU;
                    break;
                }

                if (line.rfind("MYSTATE", 0) == 0) {
                    std::stringstream ss(line);
                    std::string header;
                    float px, py, pa;
                    int php, psh, pwp, pdim, pscore;
                    ss >> header >> px >> py >> pa >> php >> psh >> pwp >> pdim >> pscore;
                    peerPos = Vec2(px, py);
                    peerAngle = pa;
                    peerHP = php;
                    peerShield = psh;
                    peerWeaponIdx = pwp;
                    peerDim = (pdim == 0) ? Dimension::PHYSICAL : Dimension::VOID_DIM;
                    peerScore = pscore;
                    peerActive = true;

                    std::string token;
                    if (ss >> token && token == "SHOOT") {
                        float sx, sy, dx, dy;
                        int sdmg, ssiz, cr, cg, cb, sdim;
                        ss >> sx >> sy >> dx >> dy >> sdmg >> ssiz >> cr >> cg >> cb >> sdim;
                        Color c(cr, cg, cb);
                        Dimension d = (sdim == 0) ? Dimension::PHYSICAL : Dimension::VOID_DIM;

                        if (mpMode == "1v1") {
                            enemyProjectiles.emplace_back(Vec2(sx, sy), Vec2(dx, dy), sdmg, c, d);
                        } else {
                            projectiles.emplace_back(Vec2(sx, sy), Vec2(dx, dy), sdmg, ssiz, c, d, true);
                        }
                    }
                } else if (line.rfind("HIT", 0) == 0) {
                    std::stringstream ss(line);
                    std::string header;
                    int dmg;
                    ss >> header >> dmg;
                    player.takeDamage(dmg);
                    notify("💥 적에게 피격당했습니다! -" + std::to_string(dmg), 60);
                }
            }

            // PvP Hit check
            if (mpMode == "1v1" && peerActive) {
                for (auto& p : projectiles) {
                    if (p.alive) {
                        if ((p.pos - peerPos).length() <= 20.0f) {
                            p.alive = false;
                            char hitBuf[32];
                            snprintf(hitBuf, sizeof(hitBuf), "HIT %d", p.damage);
                            netClient.sendLine(netClient.peerSock, hitBuf);
                            particles.burst(peerPos, Color(255, 255, 100), 8, 4.0f, 15);
                        }
                    }
                }
            }
        }

        auto& chapters = getChapters();
        auto& ch = chapters[chapterIdx % chapters.size()];
        if (gameTime >= ch.duration * 60) {
            if (chapterIdx == 0) {
                if (!jobSelectActive && !jobSelectedThisChapter) {
                    triggerJobSelect();
                    jobSelectedThisChapter = true;
                    return;
                }
                if (jobSelectActive) return;
                jobSelectedThisChapter = false;
            }
            state = GameState::WIN;
            if (chapterIdx + 1 >= saveData.max_unlocked_chapter) {
                saveData.max_unlocked_chapter = std::min(chapterIdx + 2, (int)chapters.size());
            }
            grantDeathRewards();
            return;
        }

        // Level 15 Job select trigger
        if (player.level == 15 && player.job.empty() && !jobSelectActive) {
            triggerJobSelect();
            return;
        }

        gameTime++;
        difficulty = 1.0f + gameTime / 3600.0f;

        // Player update
        mouseWorld = mouseScreen + camera.offset;
        player.update(keys, mouseWorld);

        if (!player.alive) {
            state = GameState::DEATH;
            camera.shake(15, 30);
            particles.burst(player.pos, Color(255, 80, 50), 40, 8.0f, 40);
            sound.playSFX("explosion");
            return;
        }

        // Auto-shoot (hold mouse)
        Uint32 mouseState = SDL_GetMouseState(nullptr, nullptr);
        if (mouseState & SDL_BUTTON(SDL_BUTTON_LEFT)) {
            auto bullets = player.shoot(mouseWorld);
            for (auto& b : bullets) projectiles.push_back(b);
            if (!bullets.empty()) sound.playSFX("shoot");
        }

        // Camera
        camera.update(player.pos);

        // Spawn enemies (only if not 1v1 multiplayer)
        if (!isMultiplayer || mpMode != "1v1") {
            spawnTimer++;
            int spawnRate = std::max(20, 120 - gameTime / 60);
            if (spawnTimer >= spawnRate) {
                spawnTimer = 0;
                spawnEnemy();
            }
        }

        // Update enemies
        for (auto& e : enemies) {
            if (!e.alive) continue;
            auto bullets = e.update(player.pos, player.dim);
            for (auto& b : bullets) enemyProjectiles.push_back(b);
        }

        // Update projectiles
        for (auto& p : projectiles) p.update();
        for (auto& p : enemyProjectiles) p.update();

        // Update gems
        for (auto& g : gems) g.update(player.pos);

        // Update items
        for (auto& it : items) it.update();

        // Item drop timer
        itemTimer++;
        if (itemTimer >= 900) {
            itemTimer = 0;
            dropRandomItem();
        }

        // ── Collision Detection ──

        // Player projectiles vs enemies
        for (auto& proj : projectiles) {
            if (!proj.alive) continue;
            for (auto& e : enemies) {
                if (!e.alive) continue;
                if (proj.dim != e.dim) continue;
                float dist = proj.pos.dist(e.pos);
                if (dist < proj.size + e.size) {
                    e.takeDamage(proj.damage);
                    if (!proj.piercing) proj.alive = false;
                    particles.burst(proj.pos, proj.color, 6, 3.0f, 15);
                    sound.playSFX("hit");

                    if (!e.alive) {
                        // Enemy killed
                        player.score += e.xpReward;
                        player.gold += (int)(e.goldReward * (1.0f + player._job_gold_mult_bonus));
                        player.kills++;

                        // Track job stats
                        auto& w = getWeapons()[player.weaponIdx];
                        if (std::string(w.key) == "robot_arm") {
                            player.job_stats.melee_kills++;
                        } else {
                            player.job_stats.range_kills++;
                        }
                        if (player.skill_vamp_timer > 0) {
                            player.job_stats.vamp_kills++;
                        }
                        
                        // Increment combo
                        player.combo++;
                        player.combo_timer = 180;
                        player.max_combo = std::max(player.max_combo, player.combo);
                        player.job_stats.max_combo = std::max(player.job_stats.max_combo, player.combo);

                        gems.emplace_back(e.pos, e.xpReward);
                        particles.burst(e.pos, e.color, 15, 5.0f, 25);
                        sound.playSFX("explosion");
                        camera.shake(4, 6);

                        // Boss / Elite drops
                        const EnemyType& etype_def = getEnemyTypes()[e.typeIdx];
                        bool isBoss = (e.behavior == "boss" || e.maxHp >= 200 || e.etype == "elite");
                        if (isBoss) {
                            items.emplace_back(e.pos, ItemType::BOSS_CORE, Color(255, 80, 220));
                            
                            std::string etype = e.etype;
                            if (etype.find("void") != std::string::npos || etype.find("null") != std::string::npos || etype.find("rift") != std::string::npos) {
                                items.emplace_back(e.pos + Vec2(randf(-15.0f, 15.0f), randf(-15.0f, 15.0f)), ItemType::VOID_ESSENCE, Color(180, 0, 255));
                            } else if (etype.find("abyss") != std::string::npos || etype.find("depth") != std::string::npos) {
                                items.emplace_back(e.pos + Vec2(randf(-15.0f, 15.0f), randf(-15.0f, 15.0f)), ItemType::ABYSS_PEARL, Color(0, 100, 255));
                            } else {
                                items.emplace_back(e.pos + Vec2(randf(-15.0f, 15.0f), randf(-15.0f, 15.0f)), ItemType::TIME_SHARD, Color(0, 255, 200));
                            }
                            
                            notify("★ " + std::string(etype_def.name) + " 처치! 전용 재료 드롭!", 180);
                            particles.burst(e.pos, Color(255, 80, 220), 50, 10.0f, 60);
                            camera.shake(20, 25);
                        } else {
                            // Chance to drop diamond
                            if (randf01() < 0.05f) {
                                int gain = 1;
                                float gold_mult = 1.0f + player._job_gold_mult_bonus;
                                if (gold_mult > 1.0f && randf01() < (gold_mult - 1.0f)) gain++;
                                player.diamonds += gain;
                            }
                            // Chance to drop item
                            if (randf01() < 0.08f) {
                                dropItemAt(e.pos);
                            }
                        }
                    }
                    break;
                }
            }
        }

        // Enemy projectiles vs player
        for (auto& ep : enemyProjectiles) {
            if (!ep.alive) continue;
            if (ep.dim != player.dim) continue;
            float dist = ep.pos.dist(player.pos);
            if (dist < ep.size + player.size) {
                player.takeDamage(ep.damage);
                ep.alive = false;
                particles.burst(ep.pos, Color(255, 100, 100), 8, 3.0f, 15);
                camera.shake(3, 5);
            }
        }

        // Enemies vs player (contact damage)
        for (auto& e : enemies) {
            if (!e.alive) continue;
            if (e.dim != player.dim) continue;
            float dist = e.pos.dist(player.pos);
            if (dist < e.size + player.size) {
                player.takeDamage(1);
                camera.shake(2, 3);
            }
        }

        // Gems vs player
        for (auto& g : gems) {
            if (!g.alive) continue;
            float dist = g.pos.dist(player.pos);
            if (dist < 20) {
                float xpMult = 1.0f + saveData.upgrades[3] * 0.05f;
                int oldLevel = player.level;
                player.addXP((int)(g.xp * xpMult));
                g.alive = false;
                if (player.level > oldLevel) {
                    triggerLevelup();
                    sound.playSFX("levelup");
                }
            }
        }

        // Items vs player
        for (auto& it : items) {
            if (!it.alive) continue;
            float dist = it.pos.dist(player.pos);
            if (dist < 25) {
                applyItem(it.type);
                it.alive = false;
            }
        }

        // Clean up dead entities
        auto removeDead = [](auto& vec) {
            vec.erase(std::remove_if(vec.begin(), vec.end(),
                [](const auto& e) { return !e.alive; }), vec.end());
        };
        removeDead(enemies);
        removeDead(projectiles);
        removeDead(enemyProjectiles);
        removeDead(gems);
        removeDead(items);

        // Particles
        particles.update();
    }

    void spawnEnemy() {
        auto& types = getEnemyTypes();
        auto& chapters = getChapters();
        auto& ch = chapters[chapterIdx % chapters.size()];

        // Filter types by chapter enemy set
        std::vector<int> validTypes;
        for (int i = 0; i < (int)types.size(); i++) {
            auto& t = types[i];
            if (std::string(t.behavior) == "boss") {
                // Only spawn bosses at high difficulty
                if (difficulty >= 4.0f && enemies.size() < 30) {
                    validTypes.push_back(i);
                }
                continue;
            }
            std::string eset = ch.enemy_set;
            if (eset == "normal" && t.dim == Dimension::VOID_DIM) continue;
            if (eset == "abyss" && std::string(t.key).find("void") != std::string::npos) continue;
            if (eset == "void" && std::string(t.key).find("abyss") != std::string::npos) continue;
            validTypes.push_back(i);
        }

        if (validTypes.empty()) return;

        // Spawn position around player
        float angle = randf(0, 360) * DEG2RAD;
        float dist = randf(400, 700);
        Vec2 spawnPos = player.pos + Vec2::fromAngle(angle, dist);

        int typeIdx = validTypes[randi(0, (int)validTypes.size() - 1)];
        enemies.emplace_back(typeIdx, spawnPos, difficulty);

        // Max enemy cap
        if (enemies.size() > 60) {
            enemies.erase(enemies.begin());
        }
    }

    void triggerLevelup() {
        pendingLevelups++;
        if (!levelupActive) showLevelupChoices();
    }

    void showLevelupChoices() {
        levelupActive = true;
        levelupSel = 0;
        levelupChoices.clear();

        std::vector<LevelupOption> allOptions = {
            {LevelupType::FIRE_RATE, "Fire Rate Up", "Shooting speed +15%"},
            {LevelupType::DAMAGE, "Damage Up", "All damage +20%"},
            {LevelupType::MAX_HP, "Max HP Up", "Maximum HP +20"},
            {LevelupType::MAX_SHIELD, "Max Shield Up", "Maximum Shield +10"},
            {LevelupType::SPEED, "Speed Up", "Movement speed +8%"},
            {LevelupType::MULTI_SHOT, "Multi-Shot", "Fire +1 extra projectile"},
        };

        // Shuffle and pick 3
        for (int i = (int)allOptions.size() - 1; i > 0; i--) {
            int j = randi(0, i);
            std::swap(allOptions[i], allOptions[j]);
        }
        for (int i = 0; i < 3 && i < (int)allOptions.size(); i++) {
            levelupChoices.push_back(allOptions[i]);
        }
    }

    void applyLevelupChoice(int idx) {
        if (idx < 0 || idx >= (int)levelupChoices.size()) return;
        auto& choice = levelupChoices[idx];

        switch (choice.type) {
            case LevelupType::FIRE_RATE: player.fireRateMult *= 1.15f; break;
            case LevelupType::DAMAGE: player.dmgMult += 0.20f; break;
            case LevelupType::MAX_HP:
                player.maxHealth += 20;
                player.health += 20;
                break;
            case LevelupType::MAX_SHIELD:
                player.maxShield += 10;
                player.shield += 10;
                break;
            case LevelupType::SPEED: player.speedMult += 0.08f; break;
            case LevelupType::MULTI_SHOT: player.multiShot++; break;
        }

        pendingLevelups--;
        if (pendingLevelups > 0) {
            showLevelupChoices();
        } else {
            levelupActive = false;
        }
        notify(std::string("Selected: ") + choice.name, 80);
    }

    void dropItemAt(Vec2 pos) {
        auto& itemData = getItems();
        float totalWeight = 0;
        for (auto& d : itemData) totalWeight += d.drop_chance;
        float roll = randf(0, totalWeight);
        float acc = 0;
        for (auto& d : itemData) {
            acc += d.drop_chance;
            if (roll <= acc) {
                items.emplace_back(pos, d.type, d.color);
                return;
            }
        }
    }

    void dropRandomItem() {
        Vec2 pos = player.pos + Vec2(randf(-300, 300), randf(-300, 300));
        dropItemAt(pos);
    }

    void applyItem(ItemType type) {
        float gold_mult = 1.0f + player._job_gold_mult_bonus;
        float heal_mult = 1.0f + player._job_potion_heal_bonus;

        switch (type) {
            case ItemType::HEALTH: {
                int amt = (int)(25 * heal_mult);
                player.health = std::min(player.health + amt, player.maxHealth);
                notify("HP +" + std::to_string(amt), 60);
                particles.burst(player.pos, Color(255, 80, 80), 10, 4.0f, 30);
                break;
            }
            case ItemType::SHIELD: {
                int amt = (int)(15 * heal_mult);
                player.shield = std::min(player.shield + amt, player.maxShield);
                notify("Shield +" + std::to_string(amt), 60);
                particles.burst(player.pos, Color(80, 180, 255), 10, 4.0f, 30);
                break;
            }
            case ItemType::SPEED_BOOST:
                player.speedMult += 0.05f;
                notify("Speed Up!", 60);
                particles.burst(player.pos, Color(80, 255, 80), 10, 4.0f, 30);
                break;
            case ItemType::DAMAGE_BOOST:
                player.dmgMult += 0.1f;
                notify("Damage Up!", 60);
                particles.burst(player.pos, Color(255, 200, 50), 10, 4.0f, 30);
                break;
            case ItemType::XP_ORB:
                player.addXP(30);
                notify("XP +30", 60);
                particles.burst(player.pos, Color(200, 100, 255), 10, 4.0f, 30);
                break;
            case ItemType::DIAMOND: {
                int gain = 1;
                if (gold_mult > 1.0f && randf01() < (gold_mult - 1.0f)) gain++;
                saveData.diamonds += gain;
                totalDiamonds = saveData.diamonds;
                notify("Diamond +" + std::to_string(gain) + "!", 60);
                particles.burst(player.pos, Color(100, 220, 255), 15, 5.0f, 40);
                break;
            }
            case ItemType::BOSS_CORE:
                saveData.boss_cores++;
                notify("★ 보스코어 획득! 총 " + std::to_string(saveData.boss_cores) + "개 [C]키로 제작소 입장", 200);
                particles.burst(player.pos, Color(255, 80, 220), 30, 7.0f, 50);
                break;
            case ItemType::VOID_ESSENCE:
                saveData.void_essences++;
                notify("🔮 공허의 정수 획득! 총 " + std::to_string(saveData.void_essences) + "개", 200);
                particles.burst(player.pos, Color(180, 0, 255), 30, 7.0f, 50);
                break;
            case ItemType::ABYSS_PEARL:
                saveData.abyss_pearls++;
                notify("🌑 심해의 핵 획득! 총 " + std::to_string(saveData.abyss_pearls) + "개", 200);
                particles.burst(player.pos, Color(0, 100, 255), 30, 7.0f, 50);
                break;
            case ItemType::TIME_SHARD:
                saveData.time_shards++;
                notify("🌀 시공간의 파편 획득! 총 " + std::to_string(saveData.time_shards) + "개", 200);
                particles.burst(player.pos, Color(0, 255, 200), 30, 7.0f, 50);
                break;
        }
        sound.playSFX("purchase");
        saveData.save();
    }

    void grantDeathRewards() {
        totalGold += player.gold;
        totalDiamonds += player.diamonds;
        if (player.score > saveData.highScore) {
            saveData.highScore = player.score;
        }
        saveData.gold = totalGold;
        saveData.diamonds = totalDiamonds;
        if (netClient.loggedIn) {
            netClient.saveUser(saveData);
            notify("☁️ 클라우드 데이터베이스 동기화 완료!", 150);
        } else {
            saveData.save();
        }
    }

    // ── Draw ──
    void draw() {
        switch (state) {
            case GameState::MENU: drawMenu(); break;
            case GameState::COLOR_SELECT: drawColorSelect(); break;
            case GameState::PLAYING: drawPlaying(); break;
            case GameState::DEATH: drawDeath(); break;
            case GameState::WIN: drawWin(); break;
            case GameState::SHOP: drawShop(); break;
            case GameState::GACHA: drawGacha(); break;
            case GameState::CRAFTING: drawCrafting(); break;
            case GameState::JOB_SHOP: drawJobShop(); break;
            case GameState::SHIP_SHOP: drawShipShop(); break;
            case GameState::MULTIPLAYER_LOBBY: drawMultiplayerLobby(); break;
            default: drawMenu(); break;
        }
    }

    void drawMenu() {
        // Background
        SDL_SetRenderDrawColor(ren, 8, 12, 25, 255);
        SDL_RenderClear(ren);

        starField.draw(ren, Vec2(menuAnimTimer * 0.3f, menuAnimTimer * 0.1f),
                       Dimension::PHYSICAL);

        // Title
        float pulse = 0.8f + 0.2f * std::sin(menuAnimTimer * 0.05f);
        Color titleCol(255, (Uint8)(180 * pulse), 50, 255);
        ui.drawText("DIMENSION FIGHT", SCREEN_W / 2, 80, 48, titleCol);
        ui.drawText("Paradox Survival: Neon Chronicles", SCREEN_W / 2, 120, 14,
                    Color(200, 180, 150));

        // Chapter buttons
        auto& chapters = getChapters();
        for (int i = 0; i < (int)chapters.size(); i++) {
            int by = 200 + i * 55;
            bool selected = (i == menuSel);
            bool locked = (i > saveData.max_unlocked_chapter - 1);
            Color bgCol = selected ? (locked ? Color(40, 30, 50, 150) : Color(60, 40, 100, 200)) 
                                   : (locked ? Color(15, 10, 20, 130) : Color(20, 15, 40, 180));
            Color textCol = selected ? (locked ? Color(160, 160, 170) : Color(255, 220, 100)) 
                                     : (locked ? Color(100, 100, 110) : Color(180, 180, 200));
            Color descCol = selected ? (locked ? Color(120, 120, 130) : Color(200, 180, 150)) 
                                     : (locked ? Color(70, 70, 80) : Color(120, 120, 140));

            drawRect(ren, 200, by, 400, 45, bgCol);
            if (selected) {
                if (locked) {
                    SDL_SetRenderDrawColor(ren, 120, 120, 130, 150);
                } else {
                    SDL_SetRenderDrawColor(ren, 255, 180, 50, 200);
                }
                SDL_Rect border = {200, by, 400, 45};
                SDL_RenderDrawRect(ren, &border);
            }

            char buf[128];
            if (locked) {
                snprintf(buf, sizeof(buf), "CH.%s  %s [🔒 잠김]", chapters[i].id, chapters[i].name);
                ui.drawText(buf, 400, by + 15, 18, textCol);
                ui.drawText("이전 챕터를 먼저 클리어하세요", 400, by + 34, 11, descCol);
            } else {
                snprintf(buf, sizeof(buf), "CH.%s  %s", chapters[i].id, chapters[i].name);
                ui.drawText(buf, 400, by + 15, 18, textCol);
                ui.drawText(chapters[i].desc, 400, by + 34, 11, descCol);
            }
        }

        // Stats
        char statBuf[128];
        snprintf(statBuf, sizeof(statBuf), "Gold: %d  Diamonds: %d  High Score: %d",
                 totalGold, totalDiamonds, saveData.highScore);
        ui.drawText(statBuf, SCREEN_W / 2, SCREEN_H - 40, 14, Color(200, 200, 150));

        ui.drawText("ENTER: Select  |  S: Shop  |  J: Job  |  V: Ship  |  G: Gacha  |  M: Multi", SCREEN_W / 2,
                    SCREEN_H - 15, 12, Color(120, 120, 150));
    }

    void drawColorSelect() {
        SDL_SetRenderDrawColor(ren, 8, 8, 20, 255);
        SDL_RenderClear(ren);

        ui.drawText("SELECT SHIP COLOR", SCREEN_W / 2, 80, 36, Color(255, 200, 100));

        auto& colors = getShipColors();
        int startX = SCREEN_W / 2 - (int)colors.size() * 35;
        for (int i = 0; i < (int)colors.size(); i++) {
            int cx = startX + i * 70;
            int cy = 250;
            bool sel = (i == colorSelectIdx);
            Color c = colors[i].body;

            if (sel) {
                drawFilledCircle(ren, cx, cy, 30, Color(255, 255, 255, 50));
            }
            drawFilledCircle(ren, cx, cy, 22, c);
            drawFilledCircle(ren, cx, cy, 12, colors[i].accent);

            if (sel) {
                ui.drawText(colors[i].name, cx, cy + 40, 14, Color(255, 255, 200));
                ui.drawText("^", cx, cy - 35, 18, Color(255, 200, 50));
            }
        }

        ui.drawText("A/D: Select  |  ENTER: Start  |  ESC: Back", SCREEN_W / 2,
                    SCREEN_H - 40, 14, Color(150, 150, 180));
    }

    void drawPlaying() {
        Vec2 shake = camera.getShake();
        Vec2 cam = camera.offset + shake;

        // Background color based on chapter
        auto& chapters = getChapters();
        auto& ch = chapters[chapterIdx % chapters.size()];
        float progress = std::min(1.0f, gameTime / (ch.duration * 60.0f));
        Uint8 r = (Uint8)lerpf(ch.bg_start.r, ch.bg_end.r, progress);
        Uint8 g = (Uint8)lerpf(ch.bg_start.g, ch.bg_end.g, progress);
        Uint8 b = (Uint8)lerpf(ch.bg_start.b, ch.bg_end.b, progress);
        SDL_SetRenderDrawColor(ren, r, g, b, 255);
        SDL_RenderClear(ren);

        // Star field
        starField.draw(ren, cam, dimension);

        // Items
        for (auto& it : items) it.draw(ren, cam);

        // Gems
        for (auto& g : gems) g.draw(ren, cam);

        // Enemies
        for (auto& e : enemies) e.draw(ren, cam);

        // Enemy projectiles
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
        for (auto& ep : enemyProjectiles) ep.draw(ren, cam);

        // Player projectiles
        for (auto& p : projectiles) p.draw(ren, cam);

        // Player
        player.draw(ren, cam);

        // Remote Player (Multiplayer)
        if (isMultiplayer && peerActive) {
            int sx = (int)(peerPos.x - cam.x);
            int sy = (int)(peerPos.y - cam.y);
            if (sx >= -50 && sx <= SCREEN_W + 50 && sy >= -50 && sy <= SCREEN_H + 50) {
                float cosA = std::cos(peerAngle), sinA = std::sin(peerAngle);
                int currentSize = 16;
                int x1 = sx + (int)(cosA * currentSize);
                int y1 = sy + (int)(sinA * currentSize);
                int x2 = sx + (int)(std::cos(peerAngle + 2.5f) * currentSize * 0.7f);
                int y2 = sy + (int)(std::sin(peerAngle + 2.5f) * currentSize * 0.7f);
                int x3 = sx + (int)(std::cos(peerAngle - 2.5f) * currentSize * 0.7f);
                int y3 = sy + (int)(std::sin(peerAngle - 2.5f) * currentSize * 0.7f);

                Color bodyCol = (mpMode == "1v1") ? Color(255, 80, 80) : Color(0, 255, 200);
                Color accentCol(255, 255, 255);

                SDL_SetRenderDrawColor(ren, bodyCol.r, bodyCol.g, bodyCol.b, 255);
                SDL_RenderDrawLine(ren, x1, y1, x2, y2);
                SDL_RenderDrawLine(ren, x2, y2, x3, y3);
                SDL_RenderDrawLine(ren, x3, y3, x1, y1);

                drawFilledCircle(ren, sx, sy, 3, accentCol);

                char peerLabel[64];
                snprintf(peerLabel, sizeof(peerLabel), "%s (HP: %d/%d)", peerName.c_str(), peerHP, peerMaxHP);
                ui.drawText(peerLabel, sx, sy - 28, 10, Color(220, 220, 220));

                int barW = 32;
                int bx = sx - barW / 2;
                int by = sy - 18;
                drawRect(ren, bx, by, barW, 3, Color(60, 60, 60));
                int fillW = (int)((float)barW * peerHP / std::max(1, peerMaxHP));
                drawRect(ren, bx, by, fillW, 3, Color(255, 80, 80));
            }
        }

        // Particles
        particles.draw(ren, cam);

        // HUD
        ui.drawHPBar(player.health, player.maxHealth, player.shield, player.maxShield);
        ui.drawXPBar(player.xp, player.xpToNext, player.level);
        ui.drawWeaponInfo(player.weaponIdx, player.shootCD);
        ui.drawScore(player.score, player.gold, player.diamonds);
        ui.drawDimensionIndicator(dimension);
        ui.drawDashIndicator(player.dashCD);
        ui.drawFPS(fps);
        ui.drawSkillSlotBar(player.active_skills, player.skill_cooldowns);

        // Minimap
        std::vector<Vec2> ePosns;
        for (auto& e : enemies) if (e.alive) ePosns.push_back(e.pos);
        ui.drawMinimap(player.pos, ePosns, dimension);

        // Notification
        if (notifyTimer > 0) {
            float alpha = std::min(1.0f, notifyTimer / 30.0f);
            ui.drawNotify(notifyText, alpha);
        }

        // Levelup overlay
        if (levelupActive) drawLevelupOverlay();

        // Job Select overlay
        if (jobSelectActive) drawJobSelectOverlay();

        // Scanlines effect
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
        SDL_SetRenderDrawColor(ren, 0, 0, 0, 20);
        for (int y = 0; y < SCREEN_H; y += 3) {
            SDL_RenderDrawLine(ren, 0, y, SCREEN_W, y);
        }
    }

    void drawLevelupOverlay() {
        // Dim background
        drawRect(ren, 0, 0, SCREEN_W, SCREEN_H, Color(0, 0, 0, 150));

        ui.drawText("LEVEL UP!", SCREEN_W / 2, 160, 36, Color(255, 220, 50));
        ui.drawText("Choose an upgrade:", SCREEN_W / 2, 195, 14, Color(200, 200, 220));

        for (int i = 0; i < (int)levelupChoices.size(); i++) {
            int by = 220 + i * 70;
            bool sel = (i == levelupSel);
            Color bgCol = sel ? Color(80, 50, 140, 220) : Color(30, 20, 60, 200);
            Color nameCol = sel ? Color(255, 240, 100) : Color(200, 200, 220);
            Color descCol = sel ? Color(220, 200, 180) : Color(150, 150, 170);

            drawRect(ren, 200, by, 400, 60, bgCol);
            if (sel) {
                SDL_SetRenderDrawColor(ren, 255, 200, 50, 255);
                SDL_Rect border = {200, by, 400, 60};
                SDL_RenderDrawRect(ren, &border);
            }

            ui.drawText(levelupChoices[i].name, 400, by + 20, 20, nameCol);
            ui.drawText(levelupChoices[i].desc, 400, by + 42, 13, descCol);
        }
    }

    void drawDeath() {
        SDL_SetRenderDrawColor(ren, 15, 5, 5, 255);
        SDL_RenderClear(ren);

        float pulse = 0.7f + 0.3f * std::sin(menuAnimTimer * 0.04f);
        ui.drawText("DESTROYED", SCREEN_W / 2, 150, 48, Color(255, (Uint8)(60 * pulse), 50));

        char buf[128];
        snprintf(buf, sizeof(buf), "Score: %d", player.score);
        ui.drawText(buf, SCREEN_W / 2, 250, 28, Color(255, 200, 100));

        snprintf(buf, sizeof(buf), "Kills: %d  |  Level: %d", player.kills, player.level);
        ui.drawText(buf, SCREEN_W / 2, 300, 18, Color(200, 200, 220));

        snprintf(buf, sizeof(buf), "Gold: +%d  |  Diamonds: +%d", player.gold, player.diamonds);
        ui.drawText(buf, SCREEN_W / 2, 340, 16, Color(255, 215, 0));

        ui.drawText("Press R to return to lobby", SCREEN_W / 2, 450, 18,
                    Color(150 + (int)(50 * pulse), 150, 200));
    }

    void drawWin() {
        SDL_SetRenderDrawColor(ren, 5, 10, 25, 255);
        SDL_RenderClear(ren);

        ui.drawText("VICTORY!", SCREEN_W / 2, 150, 48, Color(50, 255, 150));

        char buf[128];
        snprintf(buf, sizeof(buf), "Score: %d", player.score);
        ui.drawText(buf, SCREEN_W / 2, 250, 28, Color(255, 220, 100));

        ui.drawText("Press R to return to lobby", SCREEN_W / 2, 400, 18,
                    Color(150, 200, 150));
    }

    // ── Logic/Data Helpers ──
    int getUpgradeIdx(const std::string& key) {
        auto& upgrades = getUpgrades();
        for (int i = 0; i < (int)upgrades.size(); i++) {
            if (upgrades[i].key == key) return i;
        }
        return -1;
    }

    int getSkillBaseCost(const std::string& rarity) {
        if (rarity == "COMMON") return 1000;
        if (rarity == "UNCOMMON") return 2000;
        if (rarity == "RARE") return 3000;
        if (rarity == "EPIC") return 50;
        if (rarity == "LEGENDARY") return 100;
        if (rarity == "MYTHIC") return 250;
        if (rarity == "SECRET") return 500;
        return 1000;
    }
    
    std::string getSkillCurrency(const std::string& rarity) {
        if (rarity == "COMMON" || rarity == "UNCOMMON" || rarity == "RARE") return "gold";
        return "diamond";
    }

    struct ShopItem {
        std::string key;
        std::string name;
        std::string desc;
        int cost;
        std::string currency;
        int max_lvl;
        bool is_skill;
        std::string rarity;
        std::string type;
    };

    std::vector<ShopItem> getShopItems() {
        std::vector<ShopItem> items;
        // 1. Upgrades
        for (auto& u : getUpgrades()) {
            items.push_back({u.key, u.name, u.desc, u.cost, u.currency, u.max_lvl, false, "", ""});
        }
        // 2. Active Skills
        for (auto& [skey, s] : getAnimeSkills()) {
            if (std::string(s.type) == "active") {
                items.push_back({skey, s.name, s.desc, getSkillBaseCost(s.rarity), getSkillCurrency(s.rarity), s.max_lvl, true, s.rarity, "active"});
            }
        }
        // 3. Passive Skills
        for (auto& [skey, s] : getAnimeSkills()) {
            if (std::string(s.type) == "passive") {
                items.push_back({skey, s.name, s.desc, getSkillBaseCost(s.rarity), getSkillCurrency(s.rarity), s.max_lvl, true, s.rarity, "passive"});
            }
        }
        return items;
    }

    void applyCraftedModules() {
        player.craft_drone_laser = (saveData.crafted_items["drone_laser"] > 0);
        player.craft_time_barrier = (saveData.crafted_items["time_barrier"] > 0);
        player.craft_warp_engine = (saveData.crafted_items["warp_engine"] > 0);
        player.craft_fusion = (saveData.crafted_items["fusion"] > 0);
        player.craft_rift_gauntlet = (saveData.crafted_items["rift_gauntlet"] > 0);
        player.craft_nanobot_pylon = (saveData.crafted_items["nanobot_pylon"] > 0);
        player.craft_singularity_magnet = (saveData.crafted_items["singularity_magnet"] > 0);
        player.craft_photon_shield = (saveData.crafted_items["photon_shield"] > 0);
        player.craft_void_hyperdrive = (saveData.crafted_items["void_hyperdrive"] > 0);
        player.craft_abyssal_orb = (saveData.crafted_items["abyssal_orb"] > 0);
        player.craft_void_crown = (saveData.crafted_items["void_crown"] > 0);
        player.craft_time_chronograph = (saveData.crafted_items["time_chronograph"] > 0);
        player.craft_multiverse_matrix = (saveData.crafted_items["multiverse_matrix"] > 0);
        player.craft_nano_techpack = (saveData.crafted_items["nano_techpack"] > 0);
    }

    void applyFruitAwakeningBoosts() {
        float dmg_bonus = 0.0f;
        float cd_reduction = 0.0f;
        for (auto& [fkey, lvl] : saveData.fruit_awakenings) {
            dmg_bonus += lvl * 0.15f;          // +15% damage per level
            cd_reduction += lvl * 0.06f;      // -6% cooldown per level
        }
        player.fruit_awaken_dmg_mult = 1.0f + dmg_bonus;
        player.fruit_awaken_cd_mult = std::max(0.3f, 1.0f - cd_reduction);
    }

    // ── Shop System UI & Events ──
    void buyShopItem(const ShopItem& item) {
        if (!item.is_skill) {
            int idx = getUpgradeIdx(item.key);
            if (idx != -1) {
                int cur_lvl = saveData.upgrades[idx];
                int cost = item.cost * (cur_lvl + 1);
                if (cur_lvl < item.max_lvl) {
                    if (item.currency == "gold" && totalGold >= cost) {
                        totalGold -= cost;
                        saveData.gold = totalGold;
                        saveData.upgrades[idx]++;
                        notify("업그레이드 완료: " + item.name + " Lv." + std::to_string(saveData.upgrades[idx]), 120);
                        saveData.save();
                    } else if (item.currency == "diamond" && totalDiamonds >= cost) {
                        totalDiamonds -= cost;
                        saveData.diamonds = totalDiamonds;
                        saveData.upgrades[idx]++;
                        notify("업그레이드 완료: " + item.name + " Lv." + std::to_string(saveData.upgrades[idx]), 120);
                        saveData.save();
                    } else {
                        notify("자원이 부족합니다!", 100);
                    }
                } else {
                    notify("최대 레벨 도달!", 100);
                }
            }
        } else {
            int cur_lvl = saveData.owned_skills[item.key];
            int cost = item.cost * (cur_lvl + 1);
            if (cur_lvl < item.max_lvl) {
                if (item.currency == "gold" && totalGold >= cost) {
                    totalGold -= cost;
                    saveData.gold = totalGold;
                    if (cur_lvl == 0) {
                        saveData.owned_skills[item.key] = 1;
                        if (saveData.equipped_skills.size() < 6) {
                            saveData.equipped_skills.push_back(item.key);
                            notify("스킬 해금 + 장착: " + item.name + "!", 150);
                        } else {
                            notify("스킬 해금: " + item.name + "! (슬롯 꽉참 - [I]키로 관리)", 150);
                        }
                    } else {
                        saveData.owned_skills[item.key]++;
                        notify("스킬 레벨업: " + item.name + " Lv." + std::to_string(saveData.owned_skills[item.key]), 150);
                    }
                    saveData.save();
                } else if (item.currency == "diamond" && totalDiamonds >= cost) {
                    totalDiamonds -= cost;
                    saveData.diamonds = totalDiamonds;
                    if (cur_lvl == 0) {
                        saveData.owned_skills[item.key] = 1;
                        if (saveData.equipped_skills.size() < 6) {
                            saveData.equipped_skills.push_back(item.key);
                            notify("스킬 해금 + 장착: " + item.name + "!", 150);
                        } else {
                            notify("스킬 해금: " + item.name + "! (슬롯 꽉참 - [I]키로 관리)", 150);
                        }
                    } else {
                        saveData.owned_skills[item.key]++;
                        notify("스킬 레벨업: " + item.name + " Lv." + std::to_string(saveData.owned_skills[item.key]), 150);
                    }
                    saveData.save();
                } else {
                    notify("자원이 부족합니다!", 100);
                }
            } else {
                notify("최대 레벨 도달!", 100);
            }
        }
    }

    void drawShopTooltip(int mx, int my, const std::string& key, const std::string& name, const std::string& desc, int cost, const std::string& currency, int lvl, int max_lvl, bool is_skill) {
        int tw = 320;
        int th = 160;
        int tx = (mx < 430) ? mx + 20 : mx - tw - 20;
        int ty = (my < 380) ? my + 20 : my - th - 20;
        tx = clamp(tx, 5, SCREEN_W - tw - 5);
        ty = clamp(ty, 5, SCREEN_H - th - 5);
        
        Color border_col = is_skill ? Color(255, 80, 120) : Color(255, 200, 60);
        Color title_col = is_skill ? Color(255, 180, 200) : Color(255, 220, 100);
        const char* type_label = is_skill ? "[전투 스킬]" : "[영구 업그레이드]";
        
        ui.drawRectWithBorder(tx, ty, tw, th, Color(8, 8, 20, 240), border_col, 2);
        
        ui.drawText(std::string("「") + name + "」", tx + 15, ty + 20, 15, title_col, "left");
        ui.drawText(type_label, tx + tw - 15, ty + 20, 11, border_col, "right");
        
        std::string line1 = desc;
        std::string line2 = "";
        if (desc.size() > 34) {
            line1 = desc.substr(0, 34);
            line2 = desc.substr(34);
        }
        ui.drawText(line1, tx + 15, ty + 45, 11, Color(200, 200, 220), "left");
        if (!line2.empty()) {
            ui.drawText(line2, tx + 15, ty + 60, 11, Color(200, 200, 220), "left");
        }
        
        SDL_SetRenderDrawColor(ren, 60, 60, 80, 255);
        SDL_RenderDrawLine(ren, tx + 10, ty + 78, tx + tw - 10, ty + 78);
        
        char buf[128];
        snprintf(buf, sizeof(buf), "현재 레벨: Lv.%d  /  최대 레벨: Lv.%d", lvl, max_lvl);
        ui.drawText(buf, tx + 15, ty + 95, 11, Color(255, 230, 80), "left");
        
        if (lvl < max_lvl) {
            snprintf(buf, sizeof(buf), "강화 비용: %d %s", cost, (currency == "gold" ? "G" : "D"));
            ui.drawText(buf, tx + 15, ty + 115, 11, Color(80, 255, 180), "left");
            ui.drawText("SPACE 또는 클릭으로 구매", tx + 15, ty + 135, 10, Color(150, 150, 180), "left");
        } else {
            ui.drawText("최대 레벨 도달 (MAX)", tx + 15, ty + 115, 11, Color(0, 255, 150), "left");
        }
    }

    void drawShop() {
        SDL_SetRenderDrawColor(ren, 8, 6, 16, 255);
        SDL_RenderClear(ren);
        
        starField.draw(ren, Vec2(menuAnimTimer * 0.1f, menuAnimTimer * 0.05f), Dimension::PHYSICAL);
        
        ui.drawText("NEON NEXUS MARKET", SCREEN_W / 2, 45, 24, Color(255, 220, 100));
        ui.drawText("Protocol Enhancement & Skill Acquisition", SCREEN_W / 2, 85, 13, Color(255, 120, 50));
        
        ui.drawRectWithBorder(100, 105, 600, 35, Color(50, 35, 20), Color(120, 80, 0), 1);
        char balBuf[128];
        snprintf(balBuf, sizeof(balBuf), "CREDITS: %d G   |   DIAMONDS: %d D", totalGold, totalDiamonds);
        ui.drawText(balBuf, SCREEN_W / 2, 122, 12, Color(255, 230, 80), "center");
        
        auto items = getShopItems();
        int numItems = (int)items.size();
        
        int cw = 350, ch = 60;
        int x_start = 40, x_gap = 370;
        int y_cursor = 160 + shopScrollY;
        
        ui.setClipRect(40, 145, 720, 395);
        
        int curr_idx = 0;
        int hoveredIdx = -1;
        
        // Upgrades
        if (y_cursor > 100 && y_cursor < 600) {
            ui.drawRectWithBorder(x_start - 5, y_cursor, 730, 30, Color(30, 25, 10), Color(120, 80, 0), 1);
            ui.drawText("PERMANENT UPGRADES  (6)", SCREEN_W / 2, y_cursor + 15, 12, Color(255, 200, 80), "center");
        }
        y_cursor += 35;
        for (size_t i = 0; i < getUpgrades().size(); i += 2) {
            for (int j = 0; j < 2; j++) {
                if (i + j >= getUpgrades().size()) break;
                auto& item = items[curr_idx];
                int card_x = x_start + j * x_gap;
                int card_y = y_cursor;
                
                int lvl = saveData.upgrades[i + j];
                bool sel = (shopSel == curr_idx);
                bool hov = (mouseScreen.x >= card_x && mouseScreen.x <= card_x + cw &&
                            mouseScreen.y >= card_y && mouseScreen.y <= card_y + ch);
                
                if (hov && mouseScreen.y > 145 && mouseScreen.y < 540) {
                    hoveredIdx = curr_idx;
                }
                
                Color bg = sel ? Color(50, 40, 15) : (hov ? Color(30, 25, 8) : Color(18, 15, 6));
                Color bc = sel ? Color(255, 200, 60) : (hov ? Color(160, 120, 40) : Color(70, 55, 25));
                
                ui.drawRectWithBorder(card_x, card_y, cw, ch, bg, bc, sel ? 2 : 1);
                
                int icon_x = card_x + 8;
                int icon_y = card_y + 8;
                drawRect(ren, icon_x, icon_y, 44, 44, Color(0, 0, 0, 100));
                ui.drawText("U", icon_x + 22, icon_y + 12, 13, Color(255, 200, 60), "center");
                char lvlBuf[16];
                snprintf(lvlBuf, sizeof(lvlBuf), "LV.%d", lvl);
                ui.drawText(lvlBuf, icon_x + 22, icon_y + 30, 10, bc, "center");
                
                ui.drawText(item.name, card_x + 60, card_y + 16, 12, Color(240, 240, 220), "left");
                std::string desc_short = item.desc;
                if (desc_short.size() > 28) desc_short = desc_short.substr(0, 28) + "...";
                ui.drawText(desc_short, card_x + 60, card_y + 35, 9, Color(140, 140, 160), "left");
                
                int current_cost = (lvl < item.max_lvl) ? item.cost * (lvl + 1) : -1;
                if (current_cost > 0) {
                    char costBuf[32];
                    snprintf(costBuf, sizeof(costBuf), "%d%s", current_cost, (item.currency == "gold" ? "G" : "D"));
                    bool has_enough = (item.currency == "gold" && totalGold >= current_cost) || (item.currency == "diamond" && totalDiamonds >= current_cost);
                    Color c_col = has_enough ? Color(255, 230, 80) : Color(255, 80, 80);
                    ui.drawText(costBuf, card_x + cw - 15, card_y + 22, 12, c_col, "right");
                    if (sel) ui.drawText("CLICK/SPACE", card_x + cw - 15, card_y + 40, 8, Color(180, 180, 180), "right");
                } else {
                    ui.drawText("MAX", card_x + cw - 15, card_y + 22, 12, Color(0, 255, 150), "right");
                    char maxBuf[16];
                    snprintf(maxBuf, sizeof(maxBuf), "Lv.%d", item.max_lvl);
                    ui.drawText(maxBuf, card_x + cw - 15, card_y + 40, 9, Color(100, 200, 150), "right");
                }
                
                curr_idx++;
            }
            y_cursor += ch + 8;
        }
        y_cursor += 20;
        
        // Active Skills
        int active_count = 0;
        for (auto& [skey, s] : getAnimeSkills()) if (std::string(s.type) == "active") active_count++;
        
        if (y_cursor > 100 && y_cursor < 600) {
            ui.drawRectWithBorder(x_start - 5, y_cursor, 730, 30, Color(35, 10, 15), Color(150, 30, 50), 1);
            char actTitle[64];
            snprintf(actTitle, sizeof(actTitle), "ACTIVE COMBAT SKILLS  (%d)", active_count);
            ui.drawText(actTitle, SCREEN_W / 2, y_cursor + 15, 12, Color(255, 80, 100), "center");
        }
        y_cursor += 35;
        for (int i = 0; i < active_count; i += 2) {
            for (int j = 0; j < 2; j++) {
                if (i + j >= active_count) break;
                auto& item = items[curr_idx];
                int card_x = x_start + j * x_gap;
                int card_y = y_cursor;
                
                int lvl = saveData.owned_skills[item.key];
                bool sel = (shopSel == curr_idx);
                bool hov = (mouseScreen.x >= card_x && mouseScreen.x <= card_x + cw &&
                            mouseScreen.y >= card_y && mouseScreen.y <= card_y + ch);
                
                if (hov && mouseScreen.y > 145 && mouseScreen.y < 540) {
                    hoveredIdx = curr_idx;
                }
                
                Color bg = sel ? Color(50, 15, 25) : (hov ? Color(35, 10, 18) : Color(22, 8, 12));
                Color bc = sel ? Color(255, 80, 120) : (hov ? Color(200, 50, 80) : Color(100, 25, 45));
                
                ui.drawRectWithBorder(card_x, card_y, cw, ch, bg, bc, sel ? 2 : 1);
                
                int icon_x = card_x + 8;
                int icon_y = card_y + 8;
                drawRect(ren, icon_x, icon_y, 44, 44, Color(0, 0, 0, 100));
                ui.drawText("A", icon_x + 22, icon_y + 12, 13, Color(255, 80, 100), "center");
                char lvlBuf[16];
                snprintf(lvlBuf, sizeof(lvlBuf), "LV.%d", lvl);
                ui.drawText(lvlBuf, icon_x + 22, icon_y + 30, 10, bc, "center");
                
                if (lvl > 0) {
                    bool is_equipped = (std::find(saveData.equipped_skills.begin(), saveData.equipped_skills.end(), item.key) != saveData.equipped_skills.end());
                    if (is_equipped) {
                        drawRect(ren, icon_x, card_y + 2, 44, 12, Color(0, 40, 20));
                        ui.drawText("★장착", icon_x + 22, card_y + 8, 8, Color(0, 255, 120), "center");
                    } else {
                        drawRect(ren, icon_x, card_y + 2, 44, 12, Color(20, 20, 30));
                        ui.drawText("☆미장착", icon_x + 22, card_y + 8, 8, Color(120, 120, 140), "center");
                    }
                }
                
                ui.drawText(item.name, card_x + 60, card_y + 16, 12, Color(240, 240, 220), "left");
                std::string desc_short = item.desc;
                if (desc_short.size() > 28) desc_short = desc_short.substr(0, 28) + "...";
                ui.drawText(desc_short, card_x + 60, card_y + 35, 9, Color(140, 140, 160), "left");
                
                int current_cost = (lvl < item.max_lvl) ? item.cost * (lvl + 1) : -1;
                if (current_cost > 0) {
                    char costBuf[32];
                    snprintf(costBuf, sizeof(costBuf), "%d%s", current_cost, (item.currency == "gold" ? "G" : "D"));
                    bool has_enough = (item.currency == "gold" && totalGold >= current_cost) || (item.currency == "diamond" && totalDiamonds >= current_cost);
                    Color c_col = has_enough ? Color(255, 230, 80) : Color(255, 80, 80);
                    ui.drawText(costBuf, card_x + cw - 15, card_y + 22, 12, c_col, "right");
                    if (sel) ui.drawText("CLICK/SPACE", card_x + cw - 15, card_y + 40, 8, Color(180, 180, 180), "right");
                } else {
                    ui.drawText("MAX", card_x + cw - 15, card_y + 22, 12, Color(0, 255, 150), "right");
                    char maxBuf[16];
                    snprintf(maxBuf, sizeof(maxBuf), "Lv.%d", item.max_lvl);
                    ui.drawText(maxBuf, card_x + cw - 15, card_y + 40, 9, Color(100, 200, 150), "right");
                }
                
                curr_idx++;
            }
            y_cursor += ch + 8;
        }
        y_cursor += 20;
        
        // Passive Skills
        int passive_count = 0;
        for (auto& [skey, s] : getAnimeSkills()) if (std::string(s.type) == "passive") passive_count++;
        
        if (y_cursor > 100 && y_cursor < 600) {
            ui.drawRectWithBorder(x_start - 5, y_cursor, 730, 30, Color(10, 30, 20), Color(0, 100, 60), 1);
            char passTitle[64];
            snprintf(passTitle, sizeof(passTitle), "PASSIVE ABILITIES  (%d)", passive_count);
            ui.drawText(passTitle, SCREEN_W / 2, y_cursor + 15, 12, Color(80, 255, 180), "center");
        }
        y_cursor += 35;
        for (int i = 0; i < passive_count; i += 2) {
            for (int j = 0; j < 2; j++) {
                if (i + j >= passive_count) break;
                auto& item = items[curr_idx];
                int card_x = x_start + j * x_gap;
                int card_y = y_cursor;
                
                int lvl = saveData.owned_skills[item.key];
                bool sel = (shopSel == curr_idx);
                bool hov = (mouseScreen.x >= card_x && mouseScreen.x <= card_x + cw &&
                            mouseScreen.y >= card_y && mouseScreen.y <= card_y + ch);
                
                if (hov && mouseScreen.y > 145 && mouseScreen.y < 540) {
                    hoveredIdx = curr_idx;
                }
                
                Color bg = sel ? Color(15, 50, 35) : (hov ? Color(10, 35, 22) : Color(6, 20, 14));
                Color bc = sel ? Color(0, 255, 150) : (hov ? Color(0, 180, 110) : Color(0, 80, 50));
                
                ui.drawRectWithBorder(card_x, card_y, cw, ch, bg, bc, sel ? 2 : 1);
                
                int icon_x = card_x + 8;
                int icon_y = card_y + 8;
                drawRect(ren, icon_x, icon_y, 44, 44, Color(0, 0, 0, 100));
                ui.drawText("P", icon_x + 22, icon_y + 12, 13, Color(0, 255, 150), "center");
                char lvlBuf[16];
                snprintf(lvlBuf, sizeof(lvlBuf), "LV.%d", lvl);
                ui.drawText(lvlBuf, icon_x + 22, icon_y + 30, 10, bc, "center");
                
                if (lvl > 0) {
                    bool is_equipped = (std::find(saveData.equipped_skills.begin(), saveData.equipped_skills.end(), item.key) != saveData.equipped_skills.end());
                    if (is_equipped) {
                        drawRect(ren, icon_x, card_y + 2, 44, 12, Color(0, 40, 20));
                        ui.drawText("★장착", icon_x + 22, card_y + 8, 8, Color(0, 255, 120), "center");
                    } else {
                        drawRect(ren, icon_x, card_y + 2, 44, 12, Color(20, 20, 30));
                        ui.drawText("☆미장착", icon_x + 22, card_y + 8, 8, Color(120, 120, 140), "center");
                    }
                }
                
                ui.drawText(item.name, card_x + 60, card_y + 16, 12, Color(240, 240, 220), "left");
                std::string desc_short = item.desc;
                if (desc_short.size() > 28) desc_short = desc_short.substr(0, 28) + "...";
                ui.drawText(desc_short, card_x + 60, card_y + 35, 9, Color(140, 140, 160), "left");
                
                int current_cost = (lvl < item.max_lvl) ? item.cost * (lvl + 1) : -1;
                if (current_cost > 0) {
                    char costBuf[32];
                    snprintf(costBuf, sizeof(costBuf), "%d%s", current_cost, (item.currency == "gold" ? "G" : "D"));
                    bool has_enough = (item.currency == "gold" && totalGold >= current_cost) || (item.currency == "diamond" && totalDiamonds >= current_cost);
                    Color c_col = has_enough ? Color(255, 230, 80) : Color(255, 80, 80);
                    ui.drawText(costBuf, card_x + cw - 15, card_y + 22, 12, c_col, "right");
                    if (sel) ui.drawText("CLICK/SPACE", card_x + cw - 15, card_y + 40, 8, Color(180, 180, 180), "right");
                } else {
                    ui.drawText("MAX", card_x + cw - 15, card_y + 22, 12, Color(0, 255, 150), "right");
                    char maxBuf[16];
                    snprintf(maxBuf, sizeof(maxBuf), "Lv.%d", item.max_lvl);
                    ui.drawText(maxBuf, card_x + cw - 15, card_y + 40, 9, Color(100, 200, 150), "right");
                }
                
                curr_idx++;
            }
            y_cursor += ch + 8;
        }
        
        ui.clearClipRect();
        
        // Tooltip render
        if (hoveredIdx != -1) {
            auto& item = items[hoveredIdx];
            int lvl = 0;
            if (!item.is_skill) {
                int uIdx = getUpgradeIdx(item.key);
                if (uIdx != -1) lvl = saveData.upgrades[uIdx];
            } else {
                lvl = saveData.owned_skills[item.key];
            }
            drawShopTooltip((int)mouseScreen.x, (int)mouseScreen.y, item.key, item.name, item.desc, item.cost, item.currency, lvl, item.max_lvl, item.is_skill);
        }
        
        // Buttons
        bool back_hov = (mouseScreen.x >= 200 && mouseScreen.x <= 360 && mouseScreen.y >= 555 && mouseScreen.y <= 591);
        Color backBg = back_hov ? Color(40, 45, 75) : Color(20, 25, 40);
        ui.drawRectWithBorder(200, 555, 160, 36, backBg, Color(100, 120, 255), 1);
        ui.drawText("RETURN [ESC]", 280, 573, 12, Color(200, 220, 255), "center");
        
        bool skill_hov = (mouseScreen.x >= 380 && mouseScreen.x <= 560 && mouseScreen.y >= 555 && mouseScreen.y <= 591);
        Color skillBg = skill_hov ? Color(20, 55, 35) : Color(10, 35, 25);
        ui.drawRectWithBorder(380, 555, 180, 36, skillBg, Color(0, 220, 150), 1);
        char eqBuf[64];
        snprintf(eqBuf, sizeof(eqBuf), "SKILLS [%d/6] [I]", (int)saveData.equipped_skills.size());
        ui.drawText(eqBuf, 470, 573, 12, Color(0, 255, 180), "center");
        
        bool gacha_hov = (mouseScreen.x >= 580 && mouseScreen.x <= 760 && mouseScreen.y >= 555 && mouseScreen.y <= 591);
        float pulse = 30.0f * std::sin(SDL_GetTicks() * 0.005f);
        Color g_col = gacha_hov ? Color(100 + pulse, 40, 130 + pulse) : Color(60 + pulse, 20, 80 + pulse);
        ui.drawRectWithBorder(580, 555, 180, 36, g_col, Color(200, 80, 255), 1);
        char tickBuf[64];
        snprintf(tickBuf, sizeof(tickBuf), "ANIME 뽑기 [G] T:%d", saveData.gacha_tickets);
        ui.drawText(tickBuf, 670, 573, 12, Color(230, 160, 255), "center");
        
        ui.drawText("SPACE:구매  E:장착/해제  I:스킬관리  G:열매뽑기", SCREEN_W / 2, 543, 10, Color(80, 100, 130), "center");
        
        if (skillManageOpen) {
            drawSkillManageOverlay();
        }
    }

    void drawSkillManageOverlay() {
        drawRect(ren, 0, 0, SCREEN_W, SCREEN_H, Color(0, 0, 0, 220));
        
        ui.drawText("SKILL LOADOUT MANAGER", SCREEN_W / 2, 35, 24, Color(0, 255, 200));
        ui.drawText("장착 슬롯에 스킬을 배치하여 전투에 사용하세요", SCREEN_W / 2, 65, 12, Color(140, 180, 200));
        
        int slot_w = 110, slot_h = 80;
        int gap = 8;
        int total_w = slot_w * 6 + gap * 5;
        int sx_start = (SCREEN_W - total_w) / 2;
        int sy = 90;
        
        ui.drawRectWithBorder(sx_start - 10, sy - 8, total_w + 20, slot_h + 20, Color(10, 20, 35), Color(0, 180, 200), 2);
        ui.drawText("EQUIPPED SLOTS", SCREEN_W / 2, sy - 2, 9, Color(0, 180, 200));
        
        for (int i = 0; i < 6; i++) {
            int sx = sx_start + i * (slot_w + gap);
            bool hov = (mouseScreen.x >= sx && mouseScreen.x <= sx + slot_w &&
                        mouseScreen.y >= sy + 8 && mouseScreen.y <= sy + 8 + slot_h - 12);
            
            if (i < (int)saveData.equipped_skills.size()) {
                std::string skey = saveData.equipped_skills[i];
                auto sIt = getAnimeSkills().find(skey);
                if (sIt != getAnimeSkills().end()) {
                    auto& sdata = sIt->second;
                    int lvl = saveData.owned_skills[skey];
                    Color bg = hov ? Color(30, 50, 40) : Color(20, 35, 28);
                    ui.drawRectWithBorder(sx, sy + 8, slot_w, slot_h - 12, bg, Color(0, 255, 150), 2);
                    
                    ui.drawText(std::to_string(i + 1), sx + 12, sy + 18, 11, Color(255, 220, 80));
                    
                    std::string name = sdata.name;
                    std::string shortName = (name.size() > 12) ? name.substr(0, 12) + ".." : name;
                    ui.drawText(shortName, sx + slot_w / 2, sy + 38, 11, Color(255, 255, 230));
                    
                    char lvlBuf[16];
                    snprintf(lvlBuf, sizeof(lvlBuf), "Lv.%d", lvl);
                    ui.drawText(lvlBuf, sx + slot_w / 2, sy + 54, 10, Color(0, 220, 150));
                    
                    if (hov) {
                        ui.drawText("클릭→해제", sx + slot_w / 2, sy + 68, 9, Color(255, 100, 100));
                    }
                }
            } else {
                Color bg = hov ? Color(20, 25, 35) : Color(12, 15, 22);
                ui.drawRectWithBorder(sx, sy + 8, slot_w, slot_h - 12, bg, Color(50, 60, 80), 1);
                ui.drawText(std::to_string(i + 1), sx + 12, sy + 18, 11, Color(50, 60, 75));
                ui.drawText("빈 슬롯", sx + slot_w / 2, sy + 42, 11, Color(50, 60, 75));
            }
        }
        
        int list_y = sy + slot_h + 25;
        ui.drawText("─── 보유 스킬 목록 ───", SCREEN_W / 2, list_y, 14, Color(200, 200, 220));
        list_y += 20;
        
        std::vector<std::pair<std::string, AnimeSkillData>> owned_list;
        for (auto& [skey, lvl] : saveData.owned_skills) {
            if (lvl > 0) {
                auto sIt = getAnimeSkills().find(skey);
                if (sIt != getAnimeSkills().end()) {
                    owned_list.push_back({skey, sIt->second});
                }
            }
        }
        
        if (owned_list.empty()) {
            ui.drawText("보유한 스킬이 없습니다. 상점에서 구매하세요!", SCREEN_W / 2, list_y + 40, 14, Color(120, 120, 150));
        } else {
            int card_w = 350, card_h = 48;
            int x_left = 40, x_right = 410;
            for (size_t idx = 0; idx < owned_list.size(); idx++) {
                int col_x = (idx % 2 == 0) ? x_left : x_right;
                int row_y = list_y + (idx / 2) * (card_h + 6);
                if (row_y > 530) break;
                
                std::string skey = owned_list[idx].first;
                auto& sdata = owned_list[idx].second;
                int lvl = saveData.owned_skills[skey];
                
                bool is_equipped = (std::find(saveData.equipped_skills.begin(), saveData.equipped_skills.end(), skey) != saveData.equipped_skills.end());
                bool hov = (mouseScreen.x >= col_x && mouseScreen.x <= col_x + card_w &&
                            mouseScreen.y >= row_y && mouseScreen.y <= row_y + card_h);
                
                Color bg, bc, badge_col;
                std::string badge;
                if (is_equipped) {
                    bg = hov ? Color(25, 55, 40) : Color(15, 40, 30);
                    bc = Color(0, 200, 120);
                    int slot_idx = (int)(std::find(saveData.equipped_skills.begin(), saveData.equipped_skills.end(), skey) - saveData.equipped_skills.begin()) + 1;
                    badge = "[" + std::to_string(slot_idx) + "]";
                    badge_col = Color(0, 255, 150);
                } else {
                    bg = hov ? Color(40, 30, 50) : Color(25, 20, 35);
                    bc = Color(100, 70, 140);
                    badge = "미장착";
                    badge_col = Color(140, 100, 180);
                }
                
                ui.drawRectWithBorder(col_x, row_y, card_w, card_h, bg, bc, hov ? 2 : 1);
                
                drawRect(ren, col_x + 6, row_y + 4, 36, 14, Color(0, 0, 0));
                ui.drawText(badge, col_x + 24, row_y + 11, 8, badge_col, "center");
                
                ui.drawText(sdata.name, col_x + 50, row_y + 14, 12, Color(240, 240, 230), "left");
                char lvlBuf[32];
                snprintf(lvlBuf, sizeof(lvlBuf), "Lv.%d", lvl);
                ui.drawText(lvlBuf, col_x + 50, row_y + 32, 10, bc, "left");
                
                std::string stype = sdata.type;
                std::string type_label = (stype == "passive") ? "패시브" : "액티브";
                Color type_col = (stype == "passive") ? Color(0, 255, 150) : Color(255, 80, 100);
                ui.drawText(type_label, col_x + card_w - 50, row_y + 14, 10, type_col, "center");
                
                if (hov) {
                    if (is_equipped) {
                        ui.drawText("클릭→해제", col_x + card_w - 50, row_y + 32, 9, Color(255, 100, 100), "center");
                    } else if (saveData.equipped_skills.size() < 6) {
                        ui.drawText("클릭→장착", col_x + card_w - 50, row_y + 32, 9, Color(0, 255, 120), "center");
                    } else {
                        ui.drawText("슬롯 부족", col_x + card_w - 50, row_y + 32, 9, Color(255, 80, 80), "center");
                    }
                }
            }
        }
        
        ui.drawText("장착 " + std::to_string(saveData.equipped_skills.size()) + "/6  |  ESC/I: 닫기  |  클릭으로 장착/해제", SCREEN_W / 2, 570, 12, Color(140, 160, 200), "center");
    }

    void handleSkillManageClick(int mx, int my) {
        int slot_w = 110, slot_h = 80;
        int gap = 8;
        int total_w = slot_w * 6 + gap * 5;
        int sx_start = (SCREEN_W - total_w) / 2;
        int sy = 90;
        
        for (int i = 0; i < 6; i++) {
            int sx = sx_start + i * (slot_w + gap);
            if (mx >= sx && mx <= sx + slot_w &&
                my >= sy + 8 && my <= sy + 8 + slot_h - 12) {
                if (i < (int)saveData.equipped_skills.size()) {
                    std::string skey = saveData.equipped_skills[i];
                    saveData.equipped_skills.erase(saveData.equipped_skills.begin() + i);
                    notify("스킬 해제: " + skey, 100);
                    saveData.save();
                    return;
                }
            }
        }
        
        int list_y = sy + slot_h + 25 + 20;
        std::vector<std::pair<std::string, AnimeSkillData>> owned_list;
        for (auto& [skey, lvl] : saveData.owned_skills) {
            if (lvl > 0) {
                auto sIt = getAnimeSkills().find(skey);
                if (sIt != getAnimeSkills().end()) {
                    owned_list.push_back({skey, sIt->second});
                }
            }
        }
        
        int card_w = 350, card_h = 48;
        int x_left = 40, x_right = 410;
        for (size_t idx = 0; idx < owned_list.size(); idx++) {
            int col_x = (idx % 2 == 0) ? x_left : x_right;
            int row_y = list_y + (idx / 2) * (card_h + 6);
            if (row_y > 530) break;
            
            if (mx >= col_x && mx <= col_x + card_w &&
                my >= row_y && my <= row_y + card_h) {
                std::string skey = owned_list[idx].first;
                auto it = std::find(saveData.equipped_skills.begin(), saveData.equipped_skills.end(), skey);
                if (it != saveData.equipped_skills.end()) {
                    saveData.equipped_skills.erase(it);
                    notify(std::string("스킬 해제: ") + owned_list[idx].second.name, 100);
                } else if (saveData.equipped_skills.size() < 6) {
                    saveData.equipped_skills.push_back(skey);
                    notify(std::string("스킬 장착: ") + owned_list[idx].second.name, 100);
                } else {
                    notify("슬롯이 부족합니다!", 100);
                }
                saveData.save();
                return;
            }
        }
    }

    void handleShopEvent(const SDL_Event& e) {
        if (skillManageOpen) {
            if (e.type == SDL_KEYDOWN) {
                if (e.key.keysym.scancode == SDL_SCANCODE_ESCAPE || e.key.keysym.scancode == SDL_SCANCODE_I) {
                    skillManageOpen = false;
                }
            } else if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
                handleSkillManageClick(e.button.x, e.button.y);
            }
            return;
        }

        auto items = getShopItems();
        int numItems = (int)items.size();

        if (e.type == SDL_KEYDOWN) {
            switch (e.key.keysym.scancode) {
                case SDL_SCANCODE_ESCAPE:
                    saveData.save();
                    state = GameState::MENU;
                    break;
                case SDL_SCANCODE_UP:
                case SDL_SCANCODE_W:
                    if (numItems > 0) {
                        shopSel = (shopSel - 1 + numItems) % numItems;
                    }
                    break;
                case SDL_SCANCODE_DOWN:
                case SDL_SCANCODE_S:
                    if (numItems > 0) {
                        shopSel = (shopSel + 1) % numItems;
                    }
                    break;
                case SDL_SCANCODE_SPACE:
                case SDL_SCANCODE_RETURN:
                    if (shopSel >= 0 && shopSel < numItems) {
                        buyShopItem(items[shopSel]);
                    }
                    break;
                case SDL_SCANCODE_E:
                    if (shopSel >= 0 && shopSel < numItems) {
                        auto& item = items[shopSel];
                        if (item.is_skill) {
                            int lvl = saveData.owned_skills[item.key];
                            if (lvl > 0) {
                                auto it = std::find(saveData.equipped_skills.begin(), saveData.equipped_skills.end(), item.key);
                                if (it != saveData.equipped_skills.end()) {
                                    saveData.equipped_skills.erase(it);
                                    notify("스킬 해제: " + item.name, 100);
                                } else if (saveData.equipped_skills.size() < 6) {
                                    saveData.equipped_skills.push_back(item.key);
                                    notify("스킬 장착: " + item.name, 100);
                                } else {
                                    notify("슬롯이 부족합니다!", 100);
                                }
                                saveData.save();
                            } else {
                                notify("미해금 스킬입니다!", 100);
                            }
                        }
                    }
                    break;
                case SDL_SCANCODE_I:
                    skillManageOpen = true;
                    break;
                case SDL_SCANCODE_G:
                    state = GameState::GACHA;
                    gachaTab = "뽑기";
                    gachaScrollY = 0;
                    break;
                default: break;
            }
        } else if (e.type == SDL_MOUSEWHEEL) {
            shopScrollY += e.wheel.y * 35;
            if (shopScrollY > 0) shopScrollY = 0;
            if (shopScrollY < -800) shopScrollY = -800;
        } else if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
            int mx = e.button.x;
            int my = e.button.y;

            if (mx >= 200 && mx <= 360 && my >= 555 && my <= 591) {
                saveData.save();
                state = GameState::MENU;
                return;
            }
            if (mx >= 380 && mx <= 560 && my >= 555 && my <= 591) {
                skillManageOpen = true;
                return;
            }
            if (mx >= 580 && mx <= 760 && my >= 555 && my <= 591) {
                state = GameState::GACHA;
                gachaTab = "뽑기";
                gachaScrollY = 0;
                return;
            }

            if (my >= 145 && my <= 540) {
                int cw = 350, ch = 60;
                int x_start = 40, x_gap = 370;
                int y_cursor = 160 + shopScrollY;
                int curr_idx = 0;

                y_cursor += 35;
                for (size_t i = 0; i < getUpgrades().size(); i += 2) {
                    for (int j = 0; j < 2; j++) {
                        if (i + j >= getUpgrades().size()) break;
                        int card_x = x_start + j * x_gap;
                        int card_y = y_cursor;
                        if (mx >= card_x && mx <= card_x + cw && my >= card_y && my <= card_y + ch) {
                            if (shopSel == curr_idx) {
                                buyShopItem(items[curr_idx]);
                            } else {
                                shopSel = curr_idx;
                            }
                            return;
                        }
                        curr_idx++;
                    }
                    y_cursor += ch + 8;
                }
                y_cursor += 20;

                int active_count = 0;
                for (auto& [skey, s] : getAnimeSkills()) if (std::string(s.type) == "active") active_count++;
                y_cursor += 35;
                for (int i = 0; i < active_count; i += 2) {
                    for (int j = 0; j < 2; j++) {
                        if (i + j >= active_count) break;
                        int card_x = x_start + j * x_gap;
                        int card_y = y_cursor;
                        if (mx >= card_x && mx <= card_x + cw && my >= card_y && my <= card_y + ch) {
                            if (shopSel == curr_idx) {
                                buyShopItem(items[curr_idx]);
                            } else {
                                shopSel = curr_idx;
                            }
                            return;
                        }
                        curr_idx++;
                    }
                    y_cursor += ch + 8;
                }
                y_cursor += 20;

                int passive_count = 0;
                for (auto& [skey, s] : getAnimeSkills()) if (std::string(s.type) == "passive") passive_count++;
                y_cursor += 35;
                for (int i = 0; i < passive_count; i += 2) {
                    for (int j = 0; j < 2; j++) {
                        if (i + j >= passive_count) break;
                        int card_x = x_start + j * x_gap;
                        int card_y = y_cursor;
                        if (mx >= card_x && mx <= card_x + cw && my >= card_y && my <= card_y + ch) {
                            if (shopSel == curr_idx) {
                                buyShopItem(items[curr_idx]);
                            } else {
                                shopSel = curr_idx;
                            }
                            return;
                        }
                        curr_idx++;
                    }
                    y_cursor += ch + 8;
                }
            }
        }
    }

    void useSkill(int idx) {
        if (idx < 0 || idx >= (int)player.active_skills.size()) return;
        std::string skey = player.active_skills[idx];
        auto sIt = getAnimeSkills().find(skey);
        if (sIt == getAnimeSkills().end()) return;
        auto& s = sIt->second;

        // Cooldown check
        auto cdIt = player.skill_cooldowns.find(skey);
        int currentCD = (cdIt != player.skill_cooldowns.end()) ? cdIt->second : 0;
        if (currentCD > 0) {
            float cdSec = currentCD / 60.0f;
            char buf[128];
            snprintf(buf, sizeof(buf), " 재사용 대기 중! (%.1fs)", cdSec);
            notify(std::string(s.name) + buf, 60);
            return;
        }

        // Stats track
        player.job_stats.skill_uses++;

        // Get skill level
        int lvl = 1;
        auto lvlIt = saveData.owned_skills.find(skey);
        if (lvlIt != saveData.owned_skills.end()) {
            lvl = lvlIt->second;
        }

        // Apply skill cooldown
        float cd_m = player._job_skill_cd_mult * player.fruit_awaken_cd_mult;
        player.skill_cooldowns[skey] = std::max(10, (int)(s.cd * cd_m));

        // Damage & range calculations
        int damage = (int)((s.dmg + lvl * s.dmg_scale) * player._job_skill_dmg_mult * player.dmgMult * player.fruit_awaken_dmg_mult);
        int rangeVal = s.range + lvl * s.range_scale;

        // Visual screen shake
        camera.shake(5 + lvl * 2, 15);

        // Notify
        char buf[128];
        snprintf(buf, sizeof(buf), " 발동! (Lv.%d)", lvl);
        notify(std::string(s.name) + buf, 100);

        // Skill behaviors based on key/stype
        std::string stype = s.stype;
        if (stype == "active_burst" || skey == "jjk_sukuna_domain" || skey == "op_tremor" || skey == "ds_sun_halo") {
            particles.burst(player.pos, s.color, 40 + lvl * 8, 8.0f + lvl, 30);
            for (auto& e : enemies) {
                if (e.alive && (e.pos - player.pos).length() <= rangeVal) {
                    e.takeDamage(damage);
                }
            }
        } else if (stype == "active_proj" || skey == "jjk_hollow_purple" || skey == "naruto_rasengan" || skey == "naruto_chidori" || skey == "ds_water_slash") {
            Vec2 dir = (mouseWorld - player.pos).normalized();
            projectiles.emplace_back(player.pos, dir * 14.0f, damage, 15 + lvl * 3, s.color, player.dim, true);
            if (isMultiplayer) {
                char sBuf[256];
                snprintf(sBuf, sizeof(sBuf), "SHOOT %.2f %.2f %.2f %.2f %d %d %d %d %d %d",
                         player.pos.x, player.pos.y, dir.x * 14.0f, dir.y * 14.0f, damage, 15 + lvl * 3, s.color.r, s.color.g, s.color.b, (int)player.dim);
                mpShootInfo = sBuf;
            }
        } else if (stype == "active_summon" || skey == "jjk_ten_shadows" || skey == "naruto_clone" || skey == "slev_monarch") {
            player.shield = std::min(player.maxShield, player.shield + 10 + lvl * 5);
            particles.burst(player.pos, Color(255, 255, 255), 30, 6.0f, 40);
            notify("식신/분신 소환 - 보호막 충전!", 90);
        } else if (stype == "active_buff" || skey == "naruto_baryon_mode" || skey == "op_gear5") {
            player.skill_dmg_timer = 300 + lvl * 100;
            player.speedMult = 1.3f + lvl * 0.05f;
            particles.burst(player.pos, s.color, 30, 5.0f, 25);
            notify("신체 능력 강화 버프 활성화!", 100);
        } else if (stype == "active_target" || skey == "naruto_amaterasu" || skey == "naruto_rinnegan_meteor") {
            particles.burst(mouseWorld, s.color, 45 + lvl * 10, 10.0f + lvl, 45);
            for (auto& e : enemies) {
                if (e.alive && (e.pos - mouseWorld).length() <= rangeVal) {
                    e.takeDamage(damage);
                }
            }
        } else if (skey == "jjk_infinite_void") {
            notify("영역 전개: 무량공처 - 모든 적 정지!", 180);
            particles.burst(player.pos, Color(0, 200, 255), 80, 15.0f, 60);
            for (auto& e : enemies) {
                if (e.alive) {
                    e.takeDamage(damage);
                    e.speed = 0;
                }
            }
        } else {
            particles.burst(player.pos, s.color, 30, 8.0f, 30);
            for (auto& e : enemies) {
                if (e.alive && (e.pos - player.pos).length() <= rangeVal) {
                    e.takeDamage(damage);
                }
            }
        }
    }

    // ── Gacha UI & Event Handlers ──
    void doGacha(int count) {
        std::vector<std::string> keys;
        std::vector<float> weights;
        float totalWeight = 0;
        
        auto& fruits = getAnimeFruits();
        auto& rarities = getRarityData();
        
        for (auto& [fkey, fdata] : fruits) {
            auto rIt = rarities.find(fdata.rarity);
            if (rIt != rarities.end()) {
                keys.push_back(fkey);
                weights.push_back(rIt->second.rate);
                totalWeight += rIt->second.rate;
            }
        }
        
        std::vector<std::string> results;
        for (int c = 0; c < count; c++) {
            float roll = randf(0.0f, totalWeight);
            float acc = 0.0f;
            std::string rolled = keys.back();
            for (size_t i = 0; i < keys.size(); i++) {
                acc += weights[i];
                if (roll <= acc) {
                    rolled = keys[i];
                    break;
                }
            }
            results.push_back(rolled);
        }
        
        bool has_legend = false;
        for (auto& r : results) {
            auto fIt = fruits.find(r);
            if (fIt != fruits.end() && (std::string(fIt->second.rarity) == "LEGENDARY" || std::string(fIt->second.rarity) == "MYTHIC")) {
                has_legend = true;
            }
        }
        saveData.gacha_pity_count += count;
        if (saveData.gacha_pity_count >= 80 && !has_legend) {
            std::vector<std::string> legendary_keys;
            for (auto& [fkey, fdata] : fruits) {
                if (std::string(fdata.rarity) == "LEGENDARY") {
                    legendary_keys.push_back(fkey);
                }
            }
            if (!legendary_keys.empty()) {
                results.back() = legendary_keys[randi(0, (int)legendary_keys.size() - 1)];
            }
            saveData.gacha_pity_count = 0;
        }
        
        for (auto& fkey : results) {
            saveData.owned_anime_fruits[fkey]++;
            auto fIt = fruits.find(fkey);
            if (fIt != fruits.end()) {
                for (auto& sk : fIt->second.skills) {
                    if (saveData.owned_skills.find(sk) == saveData.owned_skills.end()) {
                        saveData.owned_skills[sk] = 1;
                    }
                }
            }
        }
        
        gachaResults = results;
        gachaRevealIdx = 0;
        gachaAnimTimer = 20;
        saveData.save();
    }

    void drawGacha() {
        SDL_SetRenderDrawColor(ren, 6, 4, 14, 255);
        SDL_RenderClear(ren);
        
        starField.draw(ren, Vec2(menuAnimTimer * 0.2f, menuAnimTimer * 0.05f), Dimension::PHYSICAL);
        
        ui.drawText("ANIME FRUIT GACHA", SCREEN_W / 2, 30, 24, Color(220, 140, 255));
        ui.drawText("주술회전 · 나루토 · 진격의거인 · 나혼렙", SCREEN_W / 2, 58, 12, Color(160, 100, 200));
        
        std::vector<std::string> tabs = {"뽑기", "도감", "인벤토리", "블랙마켓"};
        for (int i = 0; i < 4; i++) {
            int tx = 140 + i * 135;
            bool is_active = (gachaTab == tabs[i]);
            Color bg = is_active ? Color(80, 30, 120) : Color(20, 10, 35);
            Color border = is_active ? Color(200, 80, 255) : Color(80, 40, 100);
            ui.drawRectWithBorder(tx, 75, 110, 28, bg, border, is_active ? 2 : 1);
            ui.drawText(tabs[i], tx + 55, 89, 13, is_active ? Color(255, 200, 255) : Color(140, 100, 160), "center");
        }
        
        if (gachaTab == "뽑기") {
            drawGachaPullTab();
        } else if (gachaTab == "도감") {
            drawGachaCollectionTab();
        } else if (gachaTab == "인벤토리") {
            drawGachaInventoryTab();
        } else if (gachaTab == "블랙마켓") {
            drawGachaBlackMarketTab();
        }
        
        bool close_hov = (mouseScreen.x >= 680 && mouseScreen.x <= 790 &&
                          mouseScreen.y >= 10 && mouseScreen.y <= 40);
        Color closeBg = close_hov ? Color(60, 20, 30) : Color(30, 10, 20);
        ui.drawRectWithBorder(680, 10, 110, 30, closeBg, Color(255, 80, 80), 1);
        ui.drawText("닫기 [ESC]", 735, 25, 12, Color(255, 120, 120), "center");
    }

    void drawGachaPullTab() {
        ui.drawRectWithBorder(20, 110, 385, 36, Color(20, 10, 40), Color(100, 60, 160), 1);
        char statsBuf[128];
        snprintf(statsBuf, sizeof(statsBuf), "D: %d  티켓: %d  천장: %d/80", totalDiamonds, saveData.gacha_tickets, saveData.gacha_pity_count);
        ui.drawText(statsBuf, 213, 128, 12, Color(220, 180, 255), "center");
        
        ui.drawRectWithBorder(20, 155, 385, 132, Color(12, 8, 25), Color(60, 30, 90), 1);
        ui.drawText("[ 등급별 확률 ]", 213, 170, 12, Color(180, 120, 220), "center");
        int ry = 190;
        for (auto& [rk, rd] : getRarityData()) {
            char rateBuf[64];
            snprintf(rateBuf, sizeof(rateBuf), "%s  %.1f%%", rd.label, rd.rate);
            ui.drawText(rateBuf, 213, ry, 11, rd.color, "center");
            ry += 16;
        }
        
        bool h1 = (mouseScreen.x >= 30 && mouseScreen.x <= 200 && mouseScreen.y >= 300 && mouseScreen.y <= 352);
        Color b1_bg = h1 ? Color(80, 40, 120) : Color(50, 20, 80);
        ui.drawRectWithBorder(30, 300, 170, 52, b1_bg, Color(200, 100, 255), 2);
        ui.drawText("1회 뽑기", 115, 314, 15, Color(255, 220, 255), "center");
        ui.drawText("D:50 또는 티켓 1장", 115, 334, 10, Color(180, 140, 210), "center");
        
        bool h10 = (mouseScreen.x >= 215 && mouseScreen.x <= 400 && mouseScreen.y >= 300 && mouseScreen.y <= 352);
        Color b10_bg = h10 ? Color(100, 50, 30) : Color(60, 30, 20);
        ui.drawRectWithBorder(215, 300, 185, 52, b10_bg, Color(255, 160, 60), 2);
        ui.drawText("10회 뽑기", 307, 314, 15, Color(255, 240, 200), "center");
        ui.drawText("D:400 (할인)", 307, 334, 10, Color(220, 180, 100), "center");
        
        if (!gachaResults.empty()) {
            drawGachaResults();
        } else {
            ui.drawRectWithBorder(420, 110, 370, 460, Color(10, 6, 22), Color(60, 30, 80), 1);
            float pulse = 30.0f * std::sin(SDL_GetTicks() * 0.003f);
            Color pCol((Uint8)(150 + pulse), (Uint8)(80 + pulse), 200);
            ui.drawText("뽑기를 눌러 운명을 시험하세요!", 605, 290, 14, pCol, "center");
            ui.drawText("🎴🎴🎴", 605, 330, 24, Color(180, 100, 220), "center");
            
            struct SeriesInfo { std::string name; std::string icons; Color col; };
            std::vector<SeriesInfo> series_info = {
                {"주술회전", "주술 강타 / 흑섬 / 허식 자", Color(80, 220, 140)},
                {"나루토",   "나선환 / 치도리 / 미수옥", Color(255, 200, 60)},
                {"진격거인", "입체기동 / 뇌창 / 거인화", Color(255, 220, 80)},
                {"나혼렙",   "어라이즈 / 그림자 추출 / 지배자", Color(100, 140, 180)}
            };
            for (size_t i = 0; i < series_info.size(); i++) {
                int sy2 = 385 + i * 42;
                ui.drawText(series_info[i].name, 478, sy2, 12, series_info[i].col, "left");
                ui.drawText(series_info[i].icons, 620, sy2, 12, series_info[i].col, "center");
            }
        }
    }

    void drawGachaResults() {
        int n = (int)gachaResults.size();
        ui.drawRectWithBorder(420, 110, 370, 460, Color(10, 6, 22), Color(120, 60, 180), 2);
        
        if (gachaAnimTimer > 0) {
            gachaAnimTimer--;
            if (gachaAnimTimer == 0 && gachaRevealIdx < n - 1) {
                gachaRevealIdx++;
                gachaAnimTimer = 18;
            }
        }
        
        int reveal = std::min(gachaRevealIdx + 1, n);
        int cw = 163, ch = 68;
        int gap = 6;
        int x0 = 430, y0 = 122;
        
        auto& fruits = getAnimeFruits();
        auto& rarities = getRarityData();
        
        for (int ci = 0; ci < reveal; ci++) {
            std::string fkey = gachaResults[ci];
            auto fIt = fruits.find(fkey);
            if (fIt == fruits.end()) continue;
            auto& fdata = fIt->second;
            std::string rarity = fdata.rarity;
            auto rIt = rarities.find(rarity);
            if (rIt == rarities.end()) continue;
            auto& rd = rIt->second;
            
            int cx2 = x0 + (ci % 2) * (cw + gap);
            int cy2 = y0 + (ci / 2) * (ch + gap);
            
            bool is_new = (ci == reveal - 1) && gachaAnimTimer == 0;
            
            Color bg(rd.glow.r / 5, rd.glow.g / 5, rd.glow.b / 5);
            ui.drawRectWithBorder(cx2, cy2, cw, ch, bg, rd.color, is_new ? 2 : 1);
            
            ui.drawText(rd.label, cx2 + 10, cy2 + 8, 9, rd.color, "left");
            ui.drawText(fdata.series, cx2 + cw - 6, cy2 + 8, 9, Color(160, 140, 180), "right");
            ui.drawText(fdata.name, cx2 + cw / 2, cy2 + 30, 11, Color(240, 230, 255), "center");
            ui.drawText(fdata.icon, cx2 + cw / 2, cy2 + 52, 12, rd.color, "center");
        }
        
        if (gachaAnimTimer == 0 && reveal == n) {
            bool ok_hov = (mouseScreen.x >= 432 && mouseScreen.x <= 588 && mouseScreen.y >= 492 && mouseScreen.y <= 524);
            Color okBg = ok_hov ? Color(60, 30, 80) : Color(30, 15, 50);
            ui.drawRectWithBorder(432, 492, 156, 32, okBg, Color(180, 80, 255), 1);
            ui.drawText("확인 [ENTER]", 510, 508, 12, Color(220, 180, 255), "center");
            
            for (auto& fkey2 : gachaResults) {
                auto fIt2 = fruits.find(fkey2);
                if (fIt2 != fruits.end() && (std::string(fIt2->second.rarity) == "LEGENDARY" || std::string(fIt2->second.rarity) == "MYTHIC" || std::string(fIt2->second.rarity) == "SECRET")) {
                    auto rIt2 = rarities.find(fIt2->second.rarity);
                    if (rIt2 != rarities.end()) {
                        ui.drawText("★ " + std::string(fIt2->second.name) + " 획득!", 605, 540, 12, rIt2->second.color, "center");
                    }
                    break;
                }
            }
        }
    }

    void drawGachaCollectionTab() {
        std::vector<std::string> series_list = {"전체", "주술회전", "나루토", "진격의거인", "나혼렙"};
        int sx0 = 10, sy0 = 112;
        for (int i = 0; i < 5; i++) {
            int tx = sx0 + i * 157;
            bool is_sel = (gachaSeriesFilter == series_list[i]);
            
            Color sc(180, 180, 255);
            if (series_list[i] == "주술회전") sc = Color(80, 220, 140);
            else if (series_list[i] == "나루토") sc = Color(255, 200, 60);
            else if (series_list[i] == "진격의거인") sc = Color(255, 220, 80);
            else if (series_list[i] == "나혼렙") sc = Color(100, 140, 180);
            
            Color bg = is_sel ? Color(sc.r / 4, sc.g / 4, sc.b / 4) : Color(10, 8, 20);
            ui.drawRectWithBorder(tx, sy0, 152, 26, bg, sc, is_sel ? 2 : 1);
            ui.drawText(series_list[i], tx + 76, sy0 + 13, 11, sc, "center");
        }
        
        ui.setClipRect(0, 145, SCREEN_W, 415);
        int cw = 180, ch = 80;
        int gap = 6;
        int x0 = 14;
        int y0 = 150 + gachaScrollY;
        
        auto& fruits = getAnimeFruits();
        auto& rarities = getRarityData();
        int ci = 0;
        
        for (auto& [fkey, fdata] : fruits) {
            if (gachaSeriesFilter != "전체" && std::string(fdata.series) != gachaSeriesFilter) {
                continue;
            }
            int count = saveData.owned_anime_fruits[fkey];
            std::string rarity = fdata.rarity;
            auto rIt = rarities.find(rarity);
            if (rIt == rarities.end()) continue;
            auto& rd = rIt->second;
            
            int cx2 = x0 + (ci % 4) * (cw + gap);
            int cy2 = y0 + (ci / 4) * (ch + gap);
            
            bool not_owned = (count == 0);
            Color bg = not_owned ? Color(rd.color.r * 0.08f, rd.color.g * 0.08f, rd.color.b * 0.08f) : Color(rd.color.r * 0.22f, rd.color.g * 0.22f, rd.color.b * 0.22f);
            Color border = not_owned ? Color(rd.color.r * 0.35f, rd.color.g * 0.35f, rd.color.b * 0.35f) : rd.color;
            
            ui.drawRectWithBorder(cx2, cy2, cw, ch, bg, border, not_owned ? 1 : 2);
            
            if (not_owned) {
                ui.drawText("???", cx2 + cw / 2, cy2 + ch / 2, 14, Color(55, 50, 70), "center");
                ui.drawText(rd.label, cx2 + cw - 6, cy2 + 10, 9, Color(rd.color.r * 0.35f, rd.color.g * 0.35f, rd.color.b * 0.35f), "right");
            } else {
                ui.drawText(rd.label, cx2 + cw - 6, cy2 + 10, 9, rd.color, "right");
                ui.drawText(fdata.icon, cx2 + 18, cy2 + ch / 2, 14, rd.color, "center");
                ui.drawText(fdata.name, cx2 + 34, cy2 + 14, 11, Color(240, 230, 255), "left");
                ui.drawText(fdata.series, cx2 + 34, cy2 + 30, 9, Color(160, 140, 180), "left");
                
                char countBuf[16];
                snprintf(countBuf, sizeof(countBuf), "x%d", count);
                ui.drawText(countBuf, cx2 + cw - 6, cy2 + ch - 14, 10, Color(180, 255, 180), "right");
                
                std::string skills_str = "";
                int skCount = 0;
                for (auto& sk : fdata.skills) {
                    if (skCount >= 2) break;
                    auto skIt = getAnimeSkills().find(sk);
                    if (skIt != getAnimeSkills().end()) {
                        if (!skills_str.empty()) skills_str += "·";
                        std::string skName = skIt->second.name;
                        if (skName.size() > 12) skName = skName.substr(0, 12);
                        skills_str += skName;
                        skCount++;
                    }
                }
                ui.drawText(skills_str, cx2 + 34, cy2 + 54, 9, Color(120, 160, 180), "left");
            }
            ci++;
        }
        ui.clearClipRect();
        
        int owned_count = 0;
        for (auto& [fkey, count] : saveData.owned_anime_fruits) {
            if (count > 0) owned_count++;
        }
        int total_fruits = (int)fruits.size();
        
        char infoBuf[128];
        snprintf(infoBuf, sizeof(infoBuf), "수집: %d/%d  |  스크롤: 마우스휠  |  ESC: 닫기", owned_count, total_fruits);
        ui.drawText(infoBuf, SCREEN_W / 2, 578, 12, Color(120, 100, 160), "center");
    }

    void drawGachaInventoryTab() {
        ui.setClipRect(0, 145, SCREEN_W, 415);
        int cw = 180, ch = 80;
        int gap = 6;
        int x0 = 14;
        int y0 = 155 + gachaScrollY;
        
        auto& fruits = getAnimeFruits();
        auto& rarities = getRarityData();
        
        std::vector<std::string> rarityOrder = {"COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC", "SECRET"};
        std::vector<std::pair<std::string, AnimeFruitData>> sorted_fruits;
        for (auto& rName : rarityOrder) {
            for (auto& [fkey, fdata] : fruits) {
                if (std::string(fdata.rarity) == rName) {
                    sorted_fruits.push_back({fkey, fdata});
                }
            }
        }
        std::reverse(sorted_fruits.begin(), sorted_fruits.end());
        
        int ci = 0;
        std::string hovered_awaken_name = "";
        int hovered_awaken_level = 0;
        
        for (auto& [fkey, fdata] : sorted_fruits) {
            int count = saveData.owned_anime_fruits[fkey];
            if (count <= 0) continue;
            
            std::string rarity = fdata.rarity;
            auto rIt = rarities.find(rarity);
            if (rIt == rarities.end()) continue;
            auto& rd = rIt->second;
            
            int cx2 = x0 + (ci % 4) * (cw + gap);
            int cy2 = y0 + (ci / 4) * (ch + gap);
            
            Color bg(rd.color.r * 0.22f, rd.color.g * 0.22f, rd.color.b * 0.22f);
            ui.drawRectWithBorder(cx2, cy2, cw, ch, bg, rd.color, 2);
            
            ui.drawText(rd.label, cx2 + cw - 6, cy2 + 10, 9, rd.color, "right");
            ui.drawText(fdata.icon, cx2 + 18, cy2 + ch / 2, 14, rd.color, "center");
            
            int aw_lvl = saveData.fruit_awakenings[fkey];
            std::string name_str = fdata.name;
            if (aw_lvl > 0) name_str += " +" + std::to_string(aw_lvl);
            
            ui.drawText(name_str, cx2 + 34, cy2 + 14, 11, Color(240, 230, 255), "left");
            ui.drawText(fdata.series, cx2 + 34, cy2 + 30, 9, Color(160, 140, 180), "left");
            
            char countBuf[32];
            snprintf(countBuf, sizeof(countBuf), "보유: %d개", count);
            ui.drawText(countBuf, cx2 + 34, cy2 + 45, 9, Color(180, 255, 180), "left");
            
            bool is_equipped = (saveData.equipped_fruit == fkey);
            if (is_equipped) {
                drawRect(ren, cx2 + cw - 65, cy2 + ch - 26, 58, 20, Color(30, 100, 40));
                ui.drawText("장착중", cx2 + cw - 36, cy2 + ch - 16, 10, Color(200, 255, 200), "center");
            } else {
                bool eat_hov = (mouseScreen.x >= cx2 + cw - 65 && mouseScreen.x <= cx2 + cw - 7 &&
                                mouseScreen.y >= cy2 + ch - 26 && mouseScreen.y <= cy2 + ch - 6);
                Color eatBg = eat_hov ? Color(80, 20, 120) : Color(40, 10, 60);
                ui.drawRectWithBorder(cx2 + cw - 65, cy2 + ch - 26, 58, 20, eatBg, Color(200, 80, 255), 1);
                ui.drawText("먹기", cx2 + cw - 36, cy2 + ch - 16, 10, Color(255, 200, 255), "center");
            }
            
            bool is_aw = (std::string(fdata.rarity) == "LEGENDARY" || std::string(fdata.rarity) == "MYTHIC" || std::string(fdata.rarity) == "SECRET");
            if (!is_aw) {
                ui.drawRectWithBorder(cx2 + cw - 128, cy2 + ch - 26, 58, 20, Color(40, 40, 40), Color(80, 80, 80), 1);
                ui.drawText("각성불가", cx2 + cw - 99, cy2 + ch - 16, 9, Color(120, 120, 120), "center");
            } else if (aw_lvl >= 5) {
                drawRect(ren, cx2 + cw - 128, cy2 + ch - 26, 58, 20, Color(100, 80, 20));
                ui.drawText("MAX각성", cx2 + cw - 99, cy2 + ch - 16, 9, Color(255, 220, 100), "center");
            } else {
                bool aw_hov = (mouseScreen.x >= cx2 + cw - 128 && mouseScreen.x <= cx2 + cw - 70 &&
                               mouseScreen.y >= cy2 + ch - 26 && mouseScreen.y <= cy2 + ch - 6);
                Color awBg = aw_hov ? Color(120, 60, 20) : Color(60, 30, 10);
                ui.drawRectWithBorder(cx2 + cw - 128, cy2 + ch - 26, 58, 20, awBg, Color(255, 150, 50), 1);
                ui.drawText("각성", cx2 + cw - 99, cy2 + ch - 16, 10, Color(255, 200, 150), "center");
                
                if (aw_hov) {
                    hovered_awaken_name = fkey;
                    hovered_awaken_level = aw_lvl;
                }
            }
            
            ci++;
        }
        ui.clearClipRect();
        
        if (ci == 0) {
            ui.drawText("보유한 애니메이션 열매가 없습니다. 뽑기에서 획득하세요!", SCREEN_W / 2, SCREEN_H / 2, 14, Color(150, 130, 180), "center");
        }
        
        if (!hovered_awaken_name.empty()) {
            int aw_lvl = hovered_awaken_level;
            int cost_gold = (aw_lvl + 1) * 100000;
            int cost_dia = (aw_lvl + 1) * 100;
            int cost_shard = (aw_lvl + 1) * 5;
            int cost_essence = aw_lvl * 2;
            int cost_pearl = aw_lvl * 1;
            
            char awBuf[256];
            snprintf(awBuf, sizeof(awBuf), "[각성 비용] 골드: %dG  다이아: %dD  시공파편: %d개", cost_gold, cost_dia, cost_shard);
            std::string cost_str = awBuf;
            if (cost_essence > 0) cost_str += "  공허정수: " + std::to_string(cost_essence) + "개";
            if (cost_pearl > 0) cost_str += "  심해핵: " + std::to_string(cost_pearl) + "개";
            ui.drawText(cost_str, SCREEN_W / 2, 558, 11, Color(255, 180, 100), "center");
        } else {
            ui.drawText("각성 시 스킬 피해량 +15%, 쿨다운 -6% 중첩 버프가 적용됩니다. (최대 5단계)", SCREEN_W / 2, 558, 11, Color(200, 180, 220), "center");
        }
        
        char countBuf[64];
        snprintf(countBuf, sizeof(countBuf), "인벤토리: %d종 보유  |  스크롤: 마우스휠  |  ESC: 닫기", ci);
        ui.drawText(countBuf, SCREEN_W / 2, 578, 12, Color(120, 100, 160), "center");
    }

    void drawGachaBlackMarketTab() {
        ui.drawRectWithBorder(20, 115, 760, 40, Color(20, 10, 30), Color(120, 60, 180), 1);
        char goldBuf[128];
        snprintf(goldBuf, sizeof(goldBuf), "내 골드: %d G  |  시크릿 등급 열매는 오직 블랙마켓에서만 1억 G로 밀수할 수 있습니다.", totalGold);
        ui.drawText(goldBuf, SCREEN_W / 2, 135, 12, Color(255, 215, 100), "center");
        
        ui.setClipRect(0, 165, SCREEN_W, 395);
        
        auto& fruits = getAnimeFruits();
        auto& rarities = getRarityData();
        
        std::vector<std::string> secret_keys;
        for (auto& [fkey, fdata] : fruits) {
            if (std::string(fdata.rarity) == "SECRET") {
                secret_keys.push_back(fkey);
            }
        }
        
        int x0 = 20;
        int y0 = 175 + gachaScrollY;
        int cw = 370, ch = 100;
        int gap = 10;
        
        for (size_t ci = 0; ci < secret_keys.size(); ci++) {
            std::string fkey = secret_keys[ci];
            auto fIt = fruits.find(fkey);
            if (fIt == fruits.end()) continue;
            auto& fdata = fIt->second;
            
            auto rIt = rarities.find("SECRET");
            if (rIt == rarities.end()) continue;
            auto& rd = rIt->second;
            
            int cx2 = x0 + (ci % 2) * (cw + gap);
            int cy2 = y0 + (ci / 2) * (ch + gap);
            
            Color bg(rd.color.r * 0.22f, rd.color.g * 0.22f, rd.color.b * 0.22f);
            ui.drawRectWithBorder(cx2, cy2, cw, ch, bg, rd.color, 2);
            
            ui.drawText(rd.label, cx2 + cw - 10, cy2 + 10, 10, rd.color, "right");
            ui.drawText(fdata.icon, cx2 + 26, cy2 + ch / 2, 18, rd.color, "center");
            
            ui.drawText(fdata.name, cx2 + 50, cy2 + 18, 13, Color(255, 230, 255), "left");
            ui.drawText(fdata.series, cx2 + 50, cy2 + 36, 10, Color(160, 140, 180), "left");
            
            std::string skills_str = "스킬: ";
            for (auto& sk : fdata.skills) {
                auto skIt = getAnimeSkills().find(sk);
                if (skIt != getAnimeSkills().end()) {
                    skills_str += std::string(skIt->second.name) + " · ";
                }
            }
            if (skills_str.size() > 4) {
                skills_str = skills_str.substr(0, skills_str.size() - 3);
            }
            ui.drawText(skills_str, cx2 + 50, cy2 + 56, 10, Color(120, 180, 220), "left");
            
            int owned_count = saveData.owned_anime_fruits[fkey];
            ui.drawText("보유: " + std::to_string(owned_count) + "개", cx2 + 50, cy2 + 76, 10, Color(180, 255, 180), "left");
            
            bool btn_hov = (mouseScreen.x >= cx2 + cw - 110 && mouseScreen.x <= cx2 + cw - 10 &&
                            mouseScreen.y >= cy2 + ch - 36 && mouseScreen.y <= cy2 + ch - 8);
            Color btnBg = btn_hov ? Color(100, 20, 50) : Color(50, 10, 25);
            ui.drawRectWithBorder(cx2 + cw - 110, cy2 + ch - 36, 100, 28, btnBg, rd.color, 1);
            ui.drawText("구매 (1억 G)", cx2 + cw - 60, cy2 + ch - 22, 10, Color(255, 220, 230), "center");
        }
        ui.clearClipRect();
        ui.drawText("블랙마켓: 시크릿 열매 밀수  |  스크롤: 마우스휠  |  ESC: 닫기", SCREEN_W / 2, 578, 12, Color(120, 100, 160), "center");
    }

    void handleGachaEvent(const SDL_Event& e) {
        if (e.type == SDL_KEYDOWN) {
            if (e.key.keysym.scancode == SDL_SCANCODE_ESCAPE) {
                state = GameState::MENU;
                return;
            }
            if (e.key.keysym.scancode == SDL_SCANCODE_RETURN) {
                if (!gachaResults.empty() && gachaAnimTimer == 0 && gachaRevealIdx == (int)gachaResults.size() - 1) {
                    gachaResults.clear();
                }
                return;
            }
        }
        
        if (e.type == SDL_MOUSEWHEEL) {
            gachaScrollY += e.wheel.y * 35;
            int max_scroll = 0;
            if (gachaTab == "도감") {
                auto& fruits = getAnimeFruits();
                int ci = 0;
                for (auto& [fkey, fdata] : fruits) {
                    if (gachaSeriesFilter == "전체" || std::string(fdata.series) == gachaSeriesFilter) ci++;
                }
                int rows = (ci + 3) / 4;
                max_scroll = -std::max(0, rows * 86 - 380);
            } else if (gachaTab == "인벤토리") {
                int ci = 0;
                for (auto& [fkey, count] : saveData.owned_anime_fruits) {
                    if (count > 0) ci++;
                }
                int rows = (ci + 3) / 4;
                max_scroll = -std::max(0, rows * 86 - 380);
            } else if (gachaTab == "블랙마켓") {
                auto& fruits = getAnimeFruits();
                int ci = 0;
                for (auto& [fkey, fdata] : fruits) {
                    if (std::string(fdata.rarity) == "SECRET") ci++;
                }
                int rows = (ci + 1) / 2;
                max_scroll = -std::max(0, rows * 110 - 380);
            }
            gachaScrollY = std::min(0, std::max(max_scroll, gachaScrollY));
            return;
        }
        
        if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
            int mx = (int)mouseScreen.x;
            int my = (int)mouseScreen.y;
            
            if (mx >= 680 && mx <= 790 && my >= 10 && my <= 40) {
                state = GameState::MENU;
                return;
            }
            
            std::vector<std::string> tabs = {"뽑기", "도감", "인벤토리", "블랙마켓"};
            for (int i = 0; i < 4; i++) {
                int tx = 140 + i * 135;
                if (mx >= tx && mx <= tx + 110 && my >= 75 && my <= 103) {
                    gachaTab = tabs[i];
                    gachaScrollY = 0;
                    return;
                }
            }
            
            if (gachaTab == "뽑기") {
                if (!gachaResults.empty()) {
                    int n = (int)gachaResults.size();
                    if (gachaAnimTimer == 0 && gachaRevealIdx == n - 1) {
                        if (mx >= 432 && mx <= 588 && my >= 492 && my <= 524) {
                            gachaResults.clear();
                        }
                    }
                    return;
                }
                
                if (mx >= 30 && mx <= 200 && my >= 300 && my <= 352) {
                    if (saveData.gacha_tickets > 0) {
                        saveData.gacha_tickets--;
                        doGacha(1);
                    } else if (totalDiamonds >= 50) {
                        totalDiamonds -= 50;
                        saveData.diamonds = totalDiamonds;
                        doGacha(1);
                    } else {
                        notify("다이아몬드가 부족합니다! (50 D 필요)", 120);
                    }
                    return;
                }
                
                if (mx >= 215 && mx <= 400 && my >= 300 && my <= 352) {
                    if (totalDiamonds >= 400) {
                        totalDiamonds -= 400;
                        saveData.diamonds = totalDiamonds;
                        doGacha(10);
                    } else {
                        notify("다이아몬드가 부족합니다! (400 D 필요)", 120);
                    }
                    return;
                }
            }
            else if (gachaTab == "도감") {
                std::vector<std::string> series_list = {"전체", "주술회전", "나루토", "진격의거인", "나혼렙"};
                int sx0 = 10, sy0 = 112;
                for (int i = 0; i < 5; i++) {
                    int tx = sx0 + i * 157;
                    if (mx >= tx && mx <= tx + 152 && my >= sy0 && my <= sy0 + 26) {
                        gachaSeriesFilter = series_list[i];
                        gachaScrollY = 0;
                        return;
                    }
                }
            }
            else if (gachaTab == "인벤토리") {
                if (my < 145) return;
                int cw = 180, ch = 80;
                int gap = 6;
                int x0 = 14;
                int y0 = 155 + gachaScrollY;
                
                auto& fruits = getAnimeFruits();
                std::vector<std::string> rarityOrder = {"COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC", "SECRET"};
                std::vector<std::pair<std::string, AnimeFruitData>> sorted_fruits;
                for (auto& rName : rarityOrder) {
                    for (auto& [fkey, fdata] : fruits) {
                        if (std::string(fdata.rarity) == rName) {
                            sorted_fruits.push_back({fkey, fdata});
                        }
                    }
                }
                std::reverse(sorted_fruits.begin(), sorted_fruits.end());
                
                int ci = 0;
                for (auto& [fkey, fdata] : sorted_fruits) {
                    int count = saveData.owned_anime_fruits[fkey];
                    if (count <= 0) continue;
                    
                    int cx2 = x0 + (ci % 4) * (cw + gap);
                    int cy2 = y0 + (ci / 4) * (ch + gap);
                    
                    bool is_equipped = (saveData.equipped_fruit == fkey);
                    if (!is_equipped) {
                        if (mx >= cx2 + cw - 65 && mx <= cx2 + cw - 7 &&
                            my >= cy2 + ch - 26 && my <= cy2 + ch - 6) {
                            saveData.equipped_fruit = fkey;
                            saveData.equipped_skills = fdata.skills;
                            notify("맛있는 " + std::string(fdata.name) + "을(를) 먹어 능력을 얻었습니다!", 150);
                            saveData.save();
                            return;
                        }
                    }
                    
                    bool is_aw = (std::string(fdata.rarity) == "LEGENDARY" || std::string(fdata.rarity) == "MYTHIC" || std::string(fdata.rarity) == "SECRET");
                    int aw_lvl = saveData.fruit_awakenings[fkey];
                    if (is_aw && aw_lvl < 5) {
                        if (mx >= cx2 + cw - 128 && mx <= cx2 + cw - 70 &&
                            my >= cy2 + ch - 26 && my <= cy2 + ch - 6) {
                            
                            int cost_gold = (aw_lvl + 1) * 100000;
                            int cost_dia = (aw_lvl + 1) * 100;
                            int cost_shard = (aw_lvl + 1) * 5;
                            int cost_essence = aw_lvl * 2;
                            int cost_pearl = aw_lvl * 1;
                            
                            if (totalGold >= cost_gold &&
                                totalDiamonds >= cost_dia &&
                                saveData.time_shards >= cost_shard &&
                                saveData.void_essences >= cost_essence &&
                                saveData.abyss_pearls >= cost_pearl) {
                                
                                totalGold -= cost_gold;
                                totalDiamonds -= cost_dia;
                                saveData.gold = totalGold;
                                saveData.diamonds = totalDiamonds;
                                saveData.time_shards -= cost_shard;
                                saveData.void_essences -= cost_essence;
                                saveData.abyss_pearls -= cost_pearl;
                                
                                saveData.fruit_awakenings[fkey]++;
                                notify(std::string(fdata.name) + " +" + std::to_string(saveData.fruit_awakenings[fkey]) + "성 각성 성공!", 150);
                                sound.playSFX("purchase");
                                saveData.save();
                            } else {
                                notify("각성 재료가 부족합니다!", 120);
                            }
                            return;
                        }
                    }
                    ci++;
                }
            }
            else if (gachaTab == "블랙마켓") {
                if (my < 165) return;
                auto& fruits = getAnimeFruits();
                std::vector<std::string> secret_keys;
                for (auto& [fkey, fdata] : fruits) {
                    if (std::string(fdata.rarity) == "SECRET") {
                        secret_keys.push_back(fkey);
                    }
                }
                
                int x0 = 20;
                int y0 = 175 + gachaScrollY;
                int cw = 370, ch = 100;
                int gap = 10;
                
                for (size_t ci = 0; ci < secret_keys.size(); ci++) {
                    std::string fkey = secret_keys[ci];
                    auto fIt = fruits.find(fkey);
                    if (fIt == fruits.end()) continue;
                    auto& fdata = fIt->second;
                    
                    int cx2 = x0 + (ci % 2) * (cw + gap);
                    int cy2 = y0 + (ci / 2) * (ch + gap);
                    
                    if (mx >= cx2 + cw - 110 && mx <= cx2 + cw - 10 &&
                        my >= cy2 + ch - 36 && my <= cy2 + ch - 8) {
                        
                        if (totalGold >= 100000000) {
                            totalGold -= 100000000;
                            saveData.gold = totalGold;
                            saveData.owned_anime_fruits[fkey]++;
                            for (auto& sk : fdata.skills) {
                                if (saveData.owned_skills.find(sk) == saveData.owned_skills.end()) {
                                    saveData.owned_skills[sk] = 1;
                                }
                            }
                            notify("★ 블랙마켓에서 " + std::string(fdata.name) + "을 밀수하였습니다!", 180);
                            sound.playSFX("purchase");
                            saveData.save();
                        } else {
                            notify("골드가 부족합니다! (1억 G 필요)", 120);
                        }
                        return;
                    }
                }
            }
        }
    }

    // ── Crafting UI & Event Handlers ──
    void drawCrafting() {
        SDL_SetRenderDrawColor(ren, 8, 10, 18, 255);
        SDL_RenderClear(ren);
        
        starField.draw(ren, Vec2(menuAnimTimer * 0.15f, menuAnimTimer * 0.05f), Dimension::PHYSICAL);
        
        ui.drawText("NEON FORGE STATION", SCREEN_W / 2, 40, 24, Color(0, 255, 200));
        ui.drawText("보스 코어와 공허/심해/시공간 물질을 결합해 전설 모듈을 제작하세요", SCREEN_W / 2, 70, 12, Color(140, 180, 200));
        
        ui.drawRectWithBorder(30, 95, 740, 36, Color(15, 20, 35), Color(0, 180, 200), 1);
        char resBuf[256];
        snprintf(resBuf, sizeof(resBuf), "코어: %d  |  공허 정수: %d  |  심해 핵: %d  |  시공 파편: %d", 
                 saveData.boss_cores, saveData.void_essences, saveData.abyss_pearls, saveData.time_shards);
        ui.drawText(resBuf, SCREEN_W / 2, 113, 12, Color(255, 230, 80), "center");
        
        ui.setClipRect(30, 145, 740, 395);
        
        auto& recipes = getCraftingRecipes();
        int card_w = 740;
        int card_h = 75;
        int y_cursor = 150 + craftScrollY;
        
        for (size_t i = 0; i < recipes.size(); i++) {
            auto& r = recipes[i];
            int card_y = y_cursor + i * (card_h + 8);
            if (card_y > 540) break;
            if (card_y + card_h < 145) continue;
            
            bool has_crafted = (saveData.crafted_items[r.key] > 0);
            bool hov = (mouseScreen.x >= 30 && mouseScreen.x <= 770 &&
                        mouseScreen.y >= card_y && mouseScreen.y <= card_y + card_h);
            
            Color bg, bc;
            if (has_crafted) {
                bg = hov ? Color(20, 50, 35) : Color(10, 35, 22);
                bc = Color(0, 255, 120);
            } else {
                bg = hov ? Color(35, 25, 15) : Color(20, 15, 10);
                bc = hov ? r.color : Color(80, 60, 50);
            }
            
            ui.drawRectWithBorder(30, card_y, card_w, card_h, bg, bc, hov ? 2 : 1);
            ui.drawText(r.icon, 55, card_y + card_h / 2, 18, bc, "center");
            ui.drawText(r.name, 90, card_y + 20, 13, has_crafted ? Color(0, 255, 150) : Color(240, 240, 220), "left");
            ui.drawText(r.desc, 90, card_y + 42, 10, Color(160, 160, 170), "left");
            
            std::string reqs = "필요: ";
            if (r.boss_core > 0) reqs += "코어 " + std::to_string(r.boss_core) + " ";
            if (r.void_essence > 0) reqs += "공허 " + std::to_string(r.void_essence) + " ";
            if (r.abyss_pearl > 0) reqs += "심해 " + std::to_string(r.abyss_pearl) + " ";
            if (r.time_shard > 0) reqs += "시공 " + std::to_string(r.time_shard) + " ";
            ui.drawText(reqs, 500, card_y + 20, 10, Color(180, 180, 200), "left");
            
            if (has_crafted) {
                ui.drawText("[장착중]", 730, card_y + card_h / 2, 12, Color(0, 255, 150), "center");
            } else {
                bool can_craft = (saveData.boss_cores >= r.boss_core &&
                                  saveData.void_essences >= r.void_essence &&
                                  saveData.abyss_pearls >= r.abyss_pearl &&
                                  saveData.time_shards >= r.time_shard);
                
                bool btn_hov = (mouseScreen.x >= 670 && mouseScreen.x <= 750 &&
                                mouseScreen.y >= card_y + 20 && mouseScreen.y <= card_y + 55);
                
                Color btnBg = btn_hov ? (can_craft ? Color(80, 60, 20) : Color(60, 20, 20)) : (can_craft ? Color(40, 30, 10) : Color(30, 10, 10));
                Color btnBorder = can_craft ? Color(255, 200, 50) : Color(120, 40, 40);
                
                ui.drawRectWithBorder(670, card_y + 20, 80, 35, btnBg, btnBorder, 1);
                ui.drawText("제작하기", 710, card_y + 37, 10, can_craft ? Color(255, 230, 80) : Color(150, 100, 100), "center");
            }
        }
        ui.clearClipRect();
        
        bool close_hov = (mouseScreen.x >= 320 && mouseScreen.x <= 480 &&
                          mouseScreen.y >= 555 && mouseScreen.y <= 590);
        Color closeBg = close_hov ? Color(60, 20, 30) : Color(30, 10, 20);
        ui.drawRectWithBorder(320, 555, 160, 35, closeBg, Color(255, 80, 80), 1);
        ui.drawText("닫기 [ESC]", 400, 572, 12, Color(255, 120, 120), "center");
    }

    void handleCraftingEvent(const SDL_Event& e) {
        if (e.type == SDL_KEYDOWN) {
            if (e.key.keysym.scancode == SDL_SCANCODE_ESCAPE) {
                state = GameState::MENU;
                return;
            }
        }
        
        if (e.type == SDL_MOUSEWHEEL) {
            craftScrollY += e.wheel.y * 35;
            auto& recipes = getCraftingRecipes();
            int max_scroll = -std::max(0, (int)recipes.size() * 83 - 380);
            craftScrollY = std::min(0, std::max(max_scroll, craftScrollY));
            return;
        }
        
        if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
            int mx = (int)mouseScreen.x;
            int my = (int)mouseScreen.y;
            
            if (mx >= 320 && mx <= 480 && my >= 555 && my <= 590) {
                state = GameState::MENU;
                return;
            }
            
            if (my < 145) return;
            
            auto& recipes = getCraftingRecipes();
            int card_h = 75;
            int y_cursor = 150 + craftScrollY;
            
            for (size_t i = 0; i < recipes.size(); i++) {
                auto& r = recipes[i];
                int card_y = y_cursor + i * (card_h + 8);
                if (card_y > 540) break;
                if (card_y + card_h < 145) continue;
                
                bool has_crafted = (saveData.crafted_items[r.key] > 0);
                if (!has_crafted) {
                    if (mx >= 30 && mx <= 770 && my >= card_y && my <= card_y + card_h) {
                        if (saveData.boss_cores >= r.boss_core &&
                            saveData.void_essences >= r.void_essence &&
                            saveData.abyss_pearls >= r.abyss_pearl &&
                            saveData.time_shards >= r.time_shard) {
                            
                            saveData.boss_cores -= r.boss_core;
                            saveData.void_essences -= r.void_essence;
                            saveData.abyss_pearls -= r.abyss_pearl;
                            saveData.time_shards -= r.time_shard;
                            
                            saveData.crafted_items[r.key] = 1;
                            notify("★ 전설 모듈 제작 성공: " + std::string(r.name) + " 장착 완료!", 180);
                            sound.playSFX("purchase");
                            saveData.save();
                        } else {
                            notify("제작 재료가 부족합니다!", 120);
                        }
                        return;
                    }
                }
            }
        }
    }

    // ── Ship Shop UI & Event Handlers ──
    void drawShipShop() {
        SDL_SetRenderDrawColor(ren, 5, 8, 20, 255);
        SDL_RenderClear(ren);
        starField.draw(ren, Vec2(menuAnimTimer * 0.08f, menuAnimTimer * 0.04f), Dimension::VOID_DIM);

        ui.drawText("VESSEL COMMAND CENTER", SCREEN_W / 2, 40, 26, Color(100, 200, 255));
        ui.drawText("전함을 구매하고 레벨업하여 전투력을 강화하세요", SCREEN_W / 2, 75, 13, Color(80, 160, 220));

        // Resource bar
        ui.drawRectWithBorder(80, 93, 640, 28, Color(10, 20, 40), Color(60, 100, 160), 1);
        char resBuf[128];
        snprintf(resBuf, sizeof(resBuf), "Gold: %d G   |   Diamonds: %d D   |   심해핵: %d",
                 totalGold, totalDiamonds, saveData.abyss_pearls);
        ui.drawText(resBuf, SCREEN_W / 2, 107, 11, Color(180, 230, 255), "center");

        auto& ships = getShipTypes();
        int numShips = (int)ships.size();
        int cardW = 220, cardH = 200;
        int cols = 3;
        int startX = 40, startY = 135, gapX = 240, gapY = 215;

        for (int i = 0; i < numShips; i++) {
            auto& s = ships[i];
            int col = i % cols, row = i / cols;
            int cx = startX + col * gapX;
            int cy = startY + row * gapY;

            int lvl = 0;
            auto it = saveData.ship_levels.find(s.key);
            if (it != saveData.ship_levels.end()) lvl = it->second;
            bool owned = (lvl > 0);
            bool equipped = (saveData.equipped_ship == std::string(s.key));
            bool sel = (shipShopSel == i);
            bool hov = (mouseScreen.x >= cx && mouseScreen.x <= cx + cardW &&
                        mouseScreen.y >= cy && mouseScreen.y <= cy + cardH);

            Color bgCol = equipped ? Color(20, 40, 80, 220)
                        : sel ? Color(20, 30, 50, 200)
                        : hov ? Color(15, 25, 40, 200)
                        : Color(8, 12, 25, 200);
            Color borderCol = equipped ? Color(100, 200, 255)
                            : sel ? Color(80, 140, 220)
                            : owned ? Color(60, 100, 160)
                            : Color(40, 60, 100);

            ui.drawRectWithBorder(cx, cy, cardW, cardH, bgCol, borderCol, sel ? 2 : 1);

            // Ship icon (colored circle)
            drawFilledCircle(ren, cx + 35, cy + 40, 22, s.color);
            drawFilledCircle(ren, cx + 35, cy + 40, 12, s.accent);
            if (equipped) {
                drawFilledCircle(ren, cx + 35, cy + 40, 26, Color(100, 200, 255, 60));
                ui.drawText("장착중", cx + 35, cy + 68, 9, Color(100, 200, 255), "center");
            }

            // Ship name & level
            ui.drawText(s.name_ko, cx + 70, cy + 20, 15, owned ? Color(220, 240, 255) : Color(120, 140, 180), "left");
            if (owned) {
                char lvlBuf[32];
                snprintf(lvlBuf, sizeof(lvlBuf), "Lv.%d / %d", lvl, s.max_level);
                ui.drawText(lvlBuf, cx + 70, cy + 38, 11, Color(100, 200, 255), "left");
            } else {
                ui.drawText("미보유", cx + 70, cy + 38, 11, Color(150, 100, 100), "left");
            }

            // Description
            ui.drawText(s.desc, cx + 8, cy + 70, 9, Color(140, 160, 180), "left");

            // Stats per level
            char statBuf[128];
            int statY = cy + 86;
            if (s.hp_per_lvl > 0) {
                snprintf(statBuf, sizeof(statBuf), "HP +%d/lv", s.hp_per_lvl);
                ui.drawText(statBuf, cx + 8, statY, 9, Color(100, 255, 120), "left"); statY += 13;
            }
            if (s.shield_per_lvl > 0) {
                snprintf(statBuf, sizeof(statBuf), "Shield +%d/lv", s.shield_per_lvl);
                ui.drawText(statBuf, cx + 8, statY, 9, Color(80, 180, 255), "left"); statY += 13;
            }
            if (s.dmg_pct_per_lvl > 0) {
                snprintf(statBuf, sizeof(statBuf), "DMG +%d%%/lv", s.dmg_pct_per_lvl);
                ui.drawText(statBuf, cx + 8, statY, 9, Color(255, 160, 80), "left"); statY += 13;
            }
            if (s.speed_pct_per_lvl > 0) {
                snprintf(statBuf, sizeof(statBuf), "Speed +%d%%/lv", s.speed_pct_per_lvl);
                ui.drawText(statBuf, cx + 8, statY, 9, Color(180, 255, 100), "left"); statY += 13;
            }

            // Buy / Upgrade button area
            int btnY = cy + cardH - 42;
            if (!owned) {
                // Buy button
                bool canBuy = (s.buy_gold == 0 || totalGold >= s.buy_gold) &&
                              (s.buy_diamond == 0 || totalDiamonds >= s.buy_diamond) &&
                              (s.buy_pearl == 0 || saveData.abyss_pearls >= s.buy_pearl);
                Color btnBg = canBuy ? Color(20, 80, 160) : Color(40, 30, 30);
                Color btnBd = canBuy ? Color(80, 160, 255) : Color(100, 60, 60);
                ui.drawRectWithBorder(cx + 5, btnY, cardW - 10, 34, btnBg, btnBd, 1);

                std::string costStr = "구매: ";
                if (s.buy_gold > 0)    costStr += std::to_string(s.buy_gold) + "G ";
                if (s.buy_diamond > 0) costStr += std::to_string(s.buy_diamond) + "D ";
                if (s.buy_pearl > 0)   costStr += std::to_string(s.buy_pearl) + " 심해핵";
                ui.drawText(costStr, cx + cardW / 2, btnY + 17, 10,
                            canBuy ? Color(120, 200, 255) : Color(180, 100, 100), "center");
            } else if (lvl < s.max_level) {
                // Upgrade button
                int upgCost = s.upgrade_gold * lvl;
                bool canUpg = (totalGold >= upgCost);
                Color btnBg = canUpg ? Color(20, 60, 20) : Color(30, 30, 20);
                Color btnBd = canUpg ? Color(80, 200, 80) : Color(100, 100, 60);
                ui.drawRectWithBorder(cx + 5, btnY, cardW - 10, 34, btnBg, btnBd, 1);
                char upgBuf[64];
                snprintf(upgBuf, sizeof(upgBuf), "강화: %dG  (Lv.%d→%d)", upgCost, lvl, lvl + 1);
                ui.drawText(upgBuf, cx + cardW / 2, btnY + 17, 10,
                            canUpg ? Color(100, 220, 100) : Color(180, 180, 100), "center");
            } else {
                // MAX
                ui.drawRectWithBorder(cx + 5, btnY, cardW - 10, 34, Color(10, 30, 10), Color(0, 180, 80), 1);
                ui.drawText("MAX LEVEL", cx + cardW / 2, btnY + 17, 10, Color(0, 220, 100), "center");
            }

            // Equip hint
            if (owned && !equipped && sel) {
                ui.drawText("[E] 장착", cx + cardW / 2, cy + cardH - 6, 9, Color(180, 220, 255), "center");
            }
        }

        ui.drawText("클릭/SPACE: 구매·강화  |  E: 장착  |  방향키: 선택  |  ESC: 뒤로", SCREEN_W / 2,
                    SCREEN_H - 12, 11, Color(100, 120, 160));
    }

    void handleShipShopEvent(const SDL_Event& e) {
        auto& ships = getShipTypes();
        int numShips = (int)ships.size();

        if (e.type == SDL_KEYDOWN) {
            switch (e.key.keysym.scancode) {
                case SDL_SCANCODE_ESCAPE:
                    saveData.save();
                    state = GameState::MENU;
                    break;
                case SDL_SCANCODE_LEFT: case SDL_SCANCODE_A:
                    shipShopSel = (shipShopSel - 1 + numShips) % numShips; break;
                case SDL_SCANCODE_RIGHT: case SDL_SCANCODE_D:
                    shipShopSel = (shipShopSel + 1) % numShips; break;
                case SDL_SCANCODE_UP: case SDL_SCANCODE_W:
                    shipShopSel = (shipShopSel - 3 + numShips) % numShips; break;
                case SDL_SCANCODE_DOWN: case SDL_SCANCODE_S:
                    shipShopSel = (shipShopSel + 3) % numShips; break;
                case SDL_SCANCODE_SPACE: case SDL_SCANCODE_RETURN:
                    buyOrUpgradeShip(shipShopSel); break;
                case SDL_SCANCODE_E:
                    equipShip(shipShopSel); break;
                default: break;
            }
        } else if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
            int mx = e.button.x, my = e.button.y;
            int cardW = 220, cardH = 200;
            int cols = 3, startX = 40, startY = 135, gapX = 240, gapY = 215;
            for (int i = 0; i < numShips; i++) {
                int col = i % cols, row = i / cols;
                int cx = startX + col * gapX;
                int cy = startY + row * gapY;
                if (mx >= cx && mx <= cx + cardW && my >= cy && my <= cy + cardH) {
                    shipShopSel = i;
                    // Click on button area = buy/upgrade; upper area = equip if owned
                    int btnY = cy + cardH - 42;
                    if (my >= btnY) {
                        buyOrUpgradeShip(i);
                    } else {
                        equipShip(i);
                    }
                }
            }
        }
    }

    void buyOrUpgradeShip(int idx) {
        auto& ships = getShipTypes();
        if (idx < 0 || idx >= (int)ships.size()) return;
        auto& s = ships[idx];

        auto it = saveData.ship_levels.find(s.key);
        int lvl = (it != saveData.ship_levels.end()) ? it->second : 0;

        if (lvl == 0) {
            // Purchase
            if (s.buy_gold > 0 && totalGold < s.buy_gold) { notify("골드가 부족합니다!", 80); return; }
            if (s.buy_diamond > 0 && totalDiamonds < s.buy_diamond) { notify("다이아몬드가 부족합니다!", 80); return; }
            if (s.buy_pearl > 0 && saveData.abyss_pearls < s.buy_pearl) { notify("심해핵이 부족합니다!", 80); return; }
            totalGold -= s.buy_gold;
            totalDiamonds -= s.buy_diamond;
            saveData.abyss_pearls -= s.buy_pearl;
            saveData.gold = totalGold;
            saveData.diamonds = totalDiamonds;
            saveData.ship_levels[s.key] = 1;
            saveData.equipped_ship = s.key;
            saveData.save();
            notify(std::string("전함 구매: ") + s.name_ko + " (장착됨)", 120);
        } else if (lvl < s.max_level) {
            // Upgrade
            int upgCost = s.upgrade_gold * lvl;
            if (totalGold < upgCost) { notify("골드가 부족합니다!", 80); return; }
            totalGold -= upgCost;
            saveData.gold = totalGold;
            saveData.ship_levels[s.key] = lvl + 1;
            saveData.save();
            char buf[128];
            snprintf(buf, sizeof(buf), "%s Lv.%d → Lv.%d 강화!", s.name_ko, lvl, lvl + 1);
            notify(buf, 120);
        } else {
            notify("이미 최대 레벨입니다!", 80);
        }
    }

    void equipShip(int idx) {
        auto& ships = getShipTypes();
        if (idx < 0 || idx >= (int)ships.size()) return;
        auto& s = ships[idx];

        auto it = saveData.ship_levels.find(s.key);
        int lvl = (it != saveData.ship_levels.end()) ? it->second : 0;
        if (lvl == 0) { notify("먼저 전함을 구매하세요!", 80); return; }

        saveData.equipped_ship = s.key;
        saveData.save();
        notify(std::string(s.name_ko) + " 장착!", 100);
    }

    // ── Job Shop UI & Event Handlers ──
    void drawJobShop() {
        SDL_SetRenderDrawColor(ren, 8, 8, 16, 255);
        SDL_RenderClear(ren);
        
        starField.draw(ren, Vec2(menuAnimTimer * 0.1f, menuAnimTimer * 0.05f), Dimension::PHYSICAL);
        
        ui.drawText("NEON CLASS CENTER", SCREEN_W / 2, 35, 24, Color(0, 255, 200));
        ui.drawText("전투 직업을 획득하고 마스터리(Lv.1~5)를 강화해 한계를 극복하세요", SCREEN_W / 2, 60, 12, Color(140, 180, 200));
        
        auto& jobs = getJobData();
        std::vector<std::string> job_keys;
        for (auto& [k, v] : jobs) job_keys.push_back(k);
        
        ui.setClipRect(40, 90, 340, 440);
        int ly = 95 + shopScrollY;
        int card_h = 45;
        
        int selectedIndex = jobShopSel;
        if (selectedIndex < 0 || selectedIndex >= (int)job_keys.size()) selectedIndex = 0;
        std::string selectedJobKey = job_keys[selectedIndex];
        
        for (size_t i = 0; i < job_keys.size(); i++) {
            std::string jkey = job_keys[i];
            auto& jd = jobs.at(jkey);
            int card_y = ly + i * (card_h + 5);
            if (card_y > 520) break;
            if (card_y + card_h < 90) continue;
            
            bool is_unlocked = (std::find(saveData.unlocked_jobs.begin(), saveData.unlocked_jobs.end(), jkey) != saveData.unlocked_jobs.end());
            bool is_active = (saveData.player_job == jkey);
            bool is_selected = (jobShopSel == (int)i);
            bool hov = (mouseScreen.x >= 40 && mouseScreen.x <= 380 &&
                        mouseScreen.y >= card_y && mouseScreen.y <= card_y + card_h);
            
            Color bg, bc;
            if (is_selected) {
                bg = Color(60, 40, 100);
                bc = Color(255, 200, 50);
            } else if (is_active) {
                bg = Color(20, 60, 40);
                bc = Color(0, 255, 120);
            } else {
                bg = hov ? Color(25, 25, 45) : Color(15, 15, 25);
                bc = is_unlocked ? jd.color : Color(80, 80, 80);
            }
            
            ui.drawRectWithBorder(40, card_y, 340, card_h, bg, bc, is_selected ? 2 : 1);
            ui.drawText(jd.name, 60, card_y + 15, 12, is_unlocked ? Color(240, 240, 220) : Color(140, 140, 140), "left");
            ui.drawText(jd.job_class, 60, card_y + 32, 10, jd.color, "left");
            
            if (!is_unlocked) {
                ui.drawText("🔒잠금", 360, card_y + 22, 10, Color(255, 100, 100), "right");
            } else {
                int mastery = saveData.job_upgrades[jkey];
                if (mastery > 0) {
                    ui.drawText("마스터리 M." + std::to_string(mastery), 360, card_y + 22, 10, Color(255, 200, 50), "right");
                } else {
                    ui.drawText("보유중", 360, card_y + 22, 10, Color(150, 150, 150), "right");
                }
            }
        }
        ui.clearClipRect();
        
        auto& sd = jobs.at(selectedJobKey);
        bool sd_unlocked = (std::find(saveData.unlocked_jobs.begin(), saveData.unlocked_jobs.end(), selectedJobKey) != saveData.unlocked_jobs.end());
        int sd_mastery = saveData.job_upgrades[selectedJobKey];
        
        ui.drawRectWithBorder(400, 90, 360, 440, Color(10, 12, 22), sd.color, 2);
        ui.drawText(sd.name, 420, 120, 22, sd.color, "left");
        ui.drawText(sd.job_class, 420, 145, 12, Color(180, 180, 200), "left");
        ui.drawText(sd.desc, 420, 175, 11, Color(200, 200, 220), "left");
        
        ui.drawText("▲ BUFF", 420, 205, 11, Color(80, 230, 120), "left");
        ui.drawText(sd.buff, 420, 222, 10, Color(160, 235, 175), "left");
        
        ui.drawText("▼ NERF", 420, 250, 11, Color(230, 80, 80), "left");
        ui.drawText(sd.nerf, 420, 267, 10, Color(240, 160, 160), "left");
        
        ui.drawText("── 스탯 배율 ──", 420, 295, 11, Color(140, 180, 255), "left");
        char statsBuf[256];
        float sd_boost = 1.0f + sd_mastery * 0.20f;
        float finalDmg = 1.0f + (sd.dmg_mult - 1.0f) * sd_boost;
        float finalSpeed = 1.0f + (sd.speed_mult - 1.0f) * sd_boost;
        snprintf(statsBuf, sizeof(statsBuf), "체력: x%.1f  |  데미지: x%.2f  |  이동속도: x%.2f", 
                 sd.hp_mult, finalDmg, finalSpeed);
        ui.drawText(statsBuf, 420, 315, 10, Color(190, 215, 255), "left");
        
        if (!sd_unlocked) {
            ui.drawText("🔒 이 직업은 현재 잠겨 있습니다.", 420, 350, 11, Color(255, 100, 100), "left");
            ui.drawText("비용: 100 다이아몬드", 420, 370, 11, Color(255, 200, 50), "left");
            
            bool buy_hov = (mouseScreen.x >= 420 && mouseScreen.x <= 740 &&
                            mouseScreen.y >= 395 && mouseScreen.y <= 430);
            Color buyBg = buy_hov ? Color(100, 30, 30) : Color(60, 15, 15);
            ui.drawRectWithBorder(420, 395, 320, 35, buyBg, Color(255, 80, 80), 1);
            ui.drawText("직업 해금하기 (100 D)", 580, 412, 12, Color(255, 220, 220), "center");
        } else {
            bool is_active = (saveData.player_job == selectedJobKey);
            bool act_hov = (mouseScreen.x >= 420 && mouseScreen.x <= 570 &&
                            mouseScreen.y >= 395 && mouseScreen.y <= 430);
            if (is_active) {
                drawRect(ren, 420, 395, 150, 35, Color(10, 50, 30));
                ui.drawText("장착 상태", 495, 412, 11, Color(150, 255, 180), "center");
            } else {
                Color btnBg = act_hov ? Color(30, 80, 50) : Color(15, 50, 30);
                ui.drawRectWithBorder(420, 395, 150, 35, btnBg, Color(0, 255, 120), 1);
                ui.drawText("직업 적용하기", 495, 412, 11, Color(200, 255, 200), "center");
            }
            
            if (sd_mastery < 5) {
                int cost_dia = (sd_mastery + 1) * 30;
                int cost_gold = (sd_mastery + 1) * 10000;
                bool can_up = (totalDiamonds >= cost_dia || totalGold >= cost_gold);
                
                bool up_hov = (mouseScreen.x >= 585 && mouseScreen.x <= 745 &&
                               mouseScreen.y >= 395 && mouseScreen.y <= 430);
                Color btnBg = up_hov ? (can_up ? Color(100, 80, 30) : Color(60, 20, 20)) : (can_up ? Color(60, 45, 15) : Color(30, 10, 10));
                Color btnBorder = can_up ? Color(255, 200, 50) : Color(120, 40, 40);
                
                ui.drawRectWithBorder(585, 395, 160, 35, btnBg, btnBorder, 1);
                
                char upBuf[64];
                snprintf(upBuf, sizeof(upBuf), "마스터리 강화 (Lv.%d)", sd_mastery + 1);
                ui.drawText(upBuf, 665, 410, 11, can_up ? Color(255, 230, 80) : Color(150, 100, 100), "center");
                
                snprintf(upBuf, sizeof(upBuf), "비용: %d D 또는 %d G", cost_dia, cost_gold);
                ui.drawText(upBuf, 665, 424, 9, Color(200, 200, 200), "center");
            } else {
                drawRect(ren, 585, 395, 160, 35, Color(80, 60, 10));
                ui.drawText("M.5 최대 마스터리", 665, 415, 11, Color(255, 215, 0), "center");
            }
            
            if (is_active) {
                bool rst_hov = (mouseScreen.x >= 420 && mouseScreen.x <= 745 &&
                                mouseScreen.y >= 445 && mouseScreen.y <= 475);
                Color btnBg = rst_hov ? Color(120, 30, 30) : Color(70, 15, 15);
                ui.drawRectWithBorder(420, 445, 325, 30, btnBg, Color(255, 80, 80), 1);
                ui.drawText("직업 초기화 (일반 상태로 복구)", 582, 463, 11, Color(255, 200, 200), "center");
            }
        }
        
        bool close_hov = (mouseScreen.x >= 320 && mouseScreen.x <= 480 &&
                          mouseScreen.y >= 550 && mouseScreen.y <= 585);
        Color closeBg = close_hov ? Color(60, 20, 30) : Color(30, 10, 20);
        ui.drawRectWithBorder(320, 550, 160, 35, closeBg, Color(255, 80, 80), 1);
        ui.drawText("닫기 [ESC]", 400, 567, 12, Color(255, 120, 120), "center");
    }

    void handleJobShopEvent(const SDL_Event& e) {
        auto& jobs = getJobData();
        std::vector<std::string> job_keys;
        for (auto& [k, v] : jobs) job_keys.push_back(k);
        int numJobs = (int)job_keys.size();
        
        if (e.type == SDL_KEYDOWN) {
            switch (e.key.keysym.scancode) {
                case SDL_SCANCODE_ESCAPE:
                    state = GameState::MENU;
                    break;
                case SDL_SCANCODE_UP: case SDL_SCANCODE_W:
                    jobShopSel = (jobShopSel - 1 + numJobs) % numJobs;
                    break;
                case SDL_SCANCODE_DOWN: case SDL_SCANCODE_S:
                    jobShopSel = (jobShopSel + 1) % numJobs;
                    break;
                default: break;
            }
            return;
        }
        
        if (e.type == SDL_MOUSEWHEEL) {
            shopScrollY += e.wheel.y * 35;
            int max_scroll = -std::max(0, numJobs * 50 - 400);
            shopScrollY = std::min(0, std::max(max_scroll, shopScrollY));
            return;
        }
        
        if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
            int mx = (int)mouseScreen.x;
            int my = (int)mouseScreen.y;
            
            if (mx >= 320 && mx <= 480 && my >= 550 && my <= 585) {
                state = GameState::MENU;
                return;
            }
            
            int ly = 95 + shopScrollY;
            int card_h = 45;
            for (int i = 0; i < numJobs; i++) {
                int card_y = ly + i * (card_h + 5);
                if (card_y > 520) break;
                if (card_y + card_h < 90) continue;
                
                if (mx >= 40 && mx <= 380 && my >= card_y && my <= card_y + card_h) {
                    jobShopSel = i;
                    return;
                }
            }
            
            std::string selectedJobKey = job_keys[jobShopSel];
            bool sd_unlocked = (std::find(saveData.unlocked_jobs.begin(), saveData.unlocked_jobs.end(), selectedJobKey) != saveData.unlocked_jobs.end());
            int sd_mastery = saveData.job_upgrades[selectedJobKey];
            
            if (!sd_unlocked) {
                if (mx >= 420 && mx <= 740 && my >= 395 && my <= 430) {
                    if (totalDiamonds >= 100) {
                        totalDiamonds -= 100;
                        saveData.diamonds = totalDiamonds;
                        saveData.unlocked_jobs.push_back(selectedJobKey);
                        notify("🔓 직업 해금 성공: " + selectedJobKey + "!", 150);
                        sound.playSFX("purchase");
                        saveData.save();
                    } else {
                        notify("다이아몬드가 부족합니다! (100 D 필요)", 120);
                    }
                }
            } else {
                bool is_active = (saveData.player_job == selectedJobKey);
                
                if (mx >= 420 && mx <= 570 && my >= 395 && my <= 430) {
                    if (!is_active) {
                        saveData.player_job = selectedJobKey;
                        notify("직업 장착: " + selectedJobKey + "!", 150);
                        sound.playSFX("purchase");
                        saveData.save();
                    }
                }
                
                if (sd_mastery < 5) {
                    if (mx >= 585 && mx <= 745 && my >= 395 && my <= 430) {
                        int cost_dia = (sd_mastery + 1) * 30;
                        int cost_gold = (sd_mastery + 1) * 10000;
                        
                        if (totalDiamonds >= cost_dia) {
                            totalDiamonds -= cost_dia;
                            saveData.diamonds = totalDiamonds;
                            saveData.job_upgrades[selectedJobKey]++;
                            notify(selectedJobKey + " 마스터리 강화 완료! Lv." + std::to_string(saveData.job_upgrades[selectedJobKey]), 150);
                            sound.playSFX("purchase");
                            saveData.save();
                        } else if (totalGold >= cost_gold) {
                            totalGold -= cost_gold;
                            saveData.gold = totalGold;
                            saveData.job_upgrades[selectedJobKey]++;
                            notify(selectedJobKey + " 마스터리 강화 완료! Lv." + std::to_string(saveData.job_upgrades[selectedJobKey]), 150);
                            sound.playSFX("purchase");
                            saveData.save();
                        } else {
                            notify("골드 또는 다이아몬드가 부족합니다!", 120);
                        }
                    }
                }
                
                if (is_active) {
                    if (mx >= 420 && mx <= 745 && my >= 445 && my <= 475) {
                        saveData.player_job = "";
                        notify("직업을 해제하고 일반 상태로 돌아왔습니다.", 150);
                        sound.playSFX("purchase");
                        saveData.save();
                    }
                }
            }
        }
    }

    // ── Job Select Overlay UI & Event Handlers ──
    void triggerJobSelect() {
        auto& js = player.job_stats;
        std::vector<std::pair<std::string, int>> scores = {
            {"전사",    js.melee_kills * 2},
            {"저격수",  js.range_kills * 3},
            {"파일럿",  js.dash_count * 3 + js.dim_switches * 1},
            {"마법사",  js.skill_uses * 4},
            {"흡혈귀",  js.vamp_kills * 6},
            {"기계공",  js.weapon_switches * 5},
            {"탱커",    js.damage_taken / 8},
            {"광속",    js.dash_count * 5},
            {"차원술사", js.dim_switches * 10},
            {"학살자",  js.max_combo * 8}
        };
        
        std::sort(scores.begin(), scores.end(), [](const auto& a, const auto& b) {
            return a.second > b.second;
        });
        
        jobSelectChoices.clear();
        for (int i = 0; i < 3; i++) {
            jobSelectChoices.push_back(scores[i].first);
        }
        
        jobSelectActive = true;
        jobSelectTimer = 0;
        levelupActive = false;
        notify(" 전직 의식 — 당신의 플레이 스타일이 직업을 결정합니다!", 200);
    }

    void drawJobSelectOverlay() {
        jobSelectTimer++;
        int t = jobSelectTimer;
        int PHASE_REVEAL = 90;
        
        int bg_alpha = std::min(220, t * 4);
        drawRect(ren, 0, 0, SCREEN_W, SCREEN_H, Color(5, 8, 20, bg_alpha));
        
        for (int i = 0; i < 30; i++) {
            int sx = (i * 27 + 42) % SCREEN_W;
            int sy = (i * 19 + 77) % SCREEN_H;
            float twinkle = std::abs(std::sin(t * 0.05f + i * 0.2f));
            Color sc(200, 200, 255, (Uint8)(twinkle * 150 + 30));
            drawFilledCircle(ren, sx, sy, 2, sc);
        }
        
        if (t < PHASE_REVEAL) {
            float progress = (float)t / PHASE_REVEAL;
            
            int title_a = std::min(255, t * 6);
            ui.drawText("★ 플레이어 데이터 분석 중 ★", SCREEN_W / 2, 50, 18, Color(255, 220, 80, title_a), "center");
            
            int bar_x = 150, bar_y = 90, bar_w = 500, bar_h = 12;
            ui.drawRectWithBorder(bar_x, bar_y, bar_w, bar_h, Color(30, 40, 60), Color(80, 100, 150), 1);
            int filled = (int)(bar_w * progress);
            if (filled > 0) {
                Color scanCol((Uint8)(80 + 175 * progress), (Uint8)(200 - 100 * progress), (Uint8)(255 - 100 * progress));
                drawRect(ren, bar_x, bar_y, filled, bar_h, scanCol);
            }
            char pctBuf[32];
            snprintf(pctBuf, sizeof(pctBuf), "분석중... %d%%", (int)(progress * 100));
            ui.drawText(pctBuf, SCREEN_W / 2, 115, 12, Color(160, 200, 255), "center");
            
            auto& js = player.job_stats;
            struct StatRow { std::string label; int val; Color col; };
            std::vector<StatRow> stats_list = {
                {"⚔  근접 처치", js.melee_kills,   Color(255, 140, 100)},
                {"🎯  원거리 처치", js.range_kills, Color(100, 200, 255)},
                {"💨  대시 횟수",  js.dash_count,   Color(150, 255, 180)},
                {"✨  스킬 사용",  js.skill_uses,   Color(220, 150, 255)},
                {"🌀  차원 이동",  js.dim_switches, Color(100, 220, 255)},
                {"🔥  최대 콤보",  js.max_combo,    Color(255, 220, 60)}
            };
            
            float reveal_interval = (float)PHASE_REVEAL / (stats_list.size() + 2);
            for (size_t si = 0; si < stats_list.size(); si++) {
                float reveal_at = reveal_interval * (si + 1);
                if (t >= reveal_at) {
                    Uint8 row_alpha = (Uint8)std::min(255.0f, (t - reveal_at) * 15.0f);
                    int sy_pos = 148 + si * 28;
                    
                    drawRect(ren, 160, sy_pos - 2, 480, 22, Color(20, 30, 50, row_alpha / 2));
                    
                    int val_w = std::min(200, stats_list[si].val * 4 + 20);
                    Color barCol = stats_list[si].col;
                    barCol.a = row_alpha;
                    drawRect(ren, 360, sy_pos + 10, val_w, 4, barCol);
                    
                    char valBuf[64];
                    snprintf(valBuf, sizeof(valBuf), "%s  :  %d", stats_list[si].label.c_str(), stats_list[si].val);
                    ui.drawText(valBuf, 310, sy_pos + 6, 12, stats_list[si].col, "center");
                }
            }
            return;
        }
        
        int t2 = t - PHASE_REVEAL;
        
        float pulse = 0.5f + 0.5f * std::sin(t * 0.08f);
        Color titleCol((Uint8)(240 + 15 * pulse), (Uint8)(200 + 20 * pulse), 60);
        ui.drawText("✦  전직 의식  ✦", SCREEN_W / 2, 36, 26, titleCol, "center");
        ui.drawText("당신의 플레이 스타일이 직업을 결정했습니다!", SCREEN_W / 2, 76, 13, Color(180, 190, 230), "center");
        
        int card_w = 220, card_h = 248;
        int total_w = card_w * 3 + 24;
        int start_x = (SCREEN_W - total_w) / 2;
        
        auto& jobs = getJobData();
        
        for (int i = 0; i < 3; i++) {
            if (i >= (int)jobSelectChoices.size()) continue;
            std::string jkey = jobSelectChoices[i];
            auto jIt = jobs.find(jkey);
            if (jIt == jobs.end()) continue;
            auto& jd = jIt->second;
            
            int slide_delay = i * 12;
            int card_t = std::max(0, t2 - slide_delay);
            float raw = std::min(1.0f, card_t / 35.0f);
            float ease = 1.0f - std::pow(1.0f - raw, 3);
            int slide_y = (int)((1.0f - ease) * 300);
            
            int cx = start_x + i * (card_w + 12);
            int base_cy = 98 + slide_y;
            
            bool hovered = (mouseScreen.x >= cx && mouseScreen.x <= cx + card_w &&
                            mouseScreen.y >= base_cy && mouseScreen.y <= base_cy + card_h);
            int cy = base_cy - (hovered ? 10 : 0);
            
            ui.drawRectWithBorder(cx, cy, card_w, card_h, Color(18, 24, 42, 240), Color(0,0,0), 1);
            
            Color bandCol = jd.color;
            bandCol.a = 80;
            drawRect(ren, cx, cy, card_w, 52, bandCol);
            
            Color borderCol = jd.color;
            int bw = 2;
            if (hovered) {
                float bp = 0.7f + 0.3f * std::sin(t * 0.2f);
                bw = (int)(3 + bp * 2);
                borderCol = Color(std::min(255, jd.color.r + 60), std::min(255, jd.color.g + 60), std::min(255, jd.color.b + 60));
            } else {
                float bp = 0.5f + 0.5f * std::sin(t * 0.07f + i * 1.2f);
                borderCol = Color((int)(jd.color.r * (0.7f + 0.3f * bp)), (int)(jd.color.g * (0.7f + 0.3f * bp)), (int)(jd.color.b * (0.7f + 0.3f * bp)));
            }
            ui.drawRectBorder(cx, cy, card_w, card_h, bw, borderCol);
            
            int icon_x = cx + card_w / 2;
            int icon_y = cy + 28;
            int icon_r = hovered ? 22 : 20;
            drawFilledCircle(ren, icon_x, icon_y, icon_r, Color(255, 255, 255));
            drawFilledCircle(ren, icon_x, icon_y, icon_r - 1, jd.color);
            std::string class_char = jd.job_class;
            if (!class_char.empty()) class_char = class_char.substr(0, 3);
            ui.drawText(class_char, icon_x, icon_y, 9, Color(255, 255, 255), "center");
            
            drawFilledCircle(ren, cx + 18, cy + 18, 13, Color(255, 255, 255));
            drawFilledCircle(ren, cx + 18, cy + 18, 12, jd.color);
            ui.drawText(std::to_string(i + 1), cx + 18, cy + 18, 11, Color(0, 0, 0), "center");
            
            int name_y = cy + 60;
            ui.drawText(jd.name, cx + card_w / 2, name_y, 16, jd.color, "center");
            ui.drawText(jd.desc, cx + card_w / 2, name_y + 24, 9, Color(190, 195, 220), "center");
            
            SDL_SetRenderDrawColor(ren, jd.color.r, jd.color.g, jd.color.b, 120);
            SDL_RenderDrawLine(ren, cx + 14, cy + 100, cx + card_w - 14, cy + 100);
            
            ui.drawText("▲ BUFF", cx + card_w / 2, cy + 114, 10, Color(80, 230, 120), "center");
            std::string buffStr = jd.buff;
            size_t dotPos = buffStr.find(" · ");
            if (dotPos != std::string::npos) {
                ui.drawText(buffStr.substr(0, dotPos), cx + card_w / 2, cy + 128, 9, Color(150, 235, 175), "center");
                ui.drawText(buffStr.substr(dotPos + 3), cx + card_w / 2, cy + 143, 9, Color(150, 235, 175), "center");
            } else {
                ui.drawText(buffStr, cx + card_w / 2, cy + 128, 9, Color(150, 235, 175), "center");
            }
            
            ui.drawText("▼ NERF", cx + card_w / 2, cy + 175, 10, Color(230, 80, 80), "center");
            ui.drawText(jd.nerf, cx + card_w / 2, cy + 190, 9, Color(240, 160, 160), "center");
            
            int key_y = cy + card_h - 22;
            Color keyCol = hovered ? Color(255, 230, 60) : Color(200, 180, 40);
            ui.drawRectWithBorder(cx + card_w / 2 - 40, key_y - 3, 80, 20, Color(keyCol.r, keyCol.g, keyCol.b, hovered ? 90 : 50), keyCol, 1);
            ui.drawText(std::string("[") + std::to_string(i + 1) + "] 또는 클릭", cx + card_w / 2, key_y + 7, 9, keyCol, "center");
        }
        
        int bottom_y = 360 + 8;
        int blink = (int)(std::abs(std::sin(t * 0.07f)) * 80 + 175);
        ui.drawText("직업은 영구 적용됩니다 · 신중하게 선택하세요!", SCREEN_W / 2, bottom_y + 10, 12, Color(255, 180, 60), "center");
        ui.drawText("[ 1 / 2 / 3 ] 키 또는 카드 클릭으로 선택", SCREEN_W / 2, bottom_y + 30, 12, Color(blink, blink, 100), "center");
        
        int pv_y = bottom_y + 50;
        ui.drawRectWithBorder(160, pv_y, 480, 88, Color(12, 18, 35, 200), Color(60, 80, 130, 160), 1);
        ui.drawText("현재 스탯 미리보기", SCREEN_W / 2, pv_y + 12, 11, Color(140, 180, 255), "center");
        
        char pvBuf[256];
        snprintf(pvBuf, sizeof(pvBuf), "HP %d/%d  쉴드 %d/%d  LV %d  킬 %d", 
                 player.health, player.maxHealth, (int)player.shield, player.maxShield, player.level, player.kills);
        ui.drawText(pvBuf, SCREEN_W / 2, pv_y + 34, 11, Color(190, 215, 255), "center");
        
        snprintf(pvBuf, sizeof(pvBuf), "점수 %d  최고 콤보 %d", player.score, player.max_combo);
        ui.drawText(pvBuf, SCREEN_W / 2, pv_y + 54, 11, Color(190, 215, 255), "center");
        
        std::string curJob = player.job.empty() ? "없음" : player.job;
        ui.drawText("현재 직업: " + curJob, SCREEN_W / 2, pv_y + 72, 11, Color(255, 215, 90), "center");
    }

    void handleJobSelectEvent(const SDL_Event& e) {
        if (e.type == SDL_KEYDOWN) {
            if (e.key.keysym.scancode == SDL_SCANCODE_1) applyJobSelect(0);
            if (e.key.keysym.scancode == SDL_SCANCODE_2) applyJobSelect(1);
            if (e.key.keysym.scancode == SDL_SCANCODE_3) applyJobSelect(2);
        }
        
        if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
            int t = jobSelectTimer;
            if (t < 90) return;
            
            int card_w = 220, card_h = 248;
            int total_w = card_w * 3 + 24;
            int start_x = (SCREEN_W - total_w) / 2;
            
            for (int i = 0; i < 3; i++) {
                int cx = start_x + i * (card_w + 12);
                int cy = 98;
                if (mouseScreen.x >= cx && mouseScreen.x <= cx + card_w &&
                    mouseScreen.y >= cy && mouseScreen.y <= cy + card_h) {
                    applyJobSelect(i);
                    return;
                }
            }
        }
    }
    
    void applyJobSelect(int idx) {
        if (idx < 0 || idx >= (int)jobSelectChoices.size()) return;
        std::string jkey = jobSelectChoices[idx];
        auto jIt = getJobData().find(jkey);
        if (jIt != getJobData().end()) {
            int mastery = 0;
            auto mIt = saveData.job_upgrades.find(jkey);
            if (mIt != saveData.job_upgrades.end()) mastery = mIt->second;
            
            player.applyJob(jkey, jIt->second, mastery);
            saveData.player_job = jkey;
            saveData.save();
            
            jobSelectActive = false;
            
            particles.burst(player.pos, jIt->second.color, 60, 10.0f, 70);
            camera.shake(10, 15);
            notify("전직 완료! [" + std::string(jIt->second.name) + "]  " + std::string(jIt->second.buff), 260);
        }
    }

    void drawMultiplayerLobby() {
        // Background
        SDL_SetRenderDrawColor(ren, 10, 14, 22, 255);
        SDL_RenderClear(ren);

        // Neon starfield background
        starField.draw(ren, Vec2(mpSearchTimer * 0.1f, mpSearchTimer * 0.05f), Dimension::PHYSICAL);

        // Title (Valorant styled neon red / white)
        float pulse = 0.8f + 0.2f * std::sin(mpSearchTimer * 0.08f);
        Color titleCol(255, (Uint8)(70 + 30 * pulse), (Uint8)(85 + 30 * pulse), 255);
        ui.drawText("CHAMBER Matchmaking", SCREEN_W / 2, 45, 30, titleCol, "center");

        // Server Status HUD
        int mockPlayers = 138 + ((int)mpSearchTimer / 100) % 7 + (int)(5 * std::sin(mpSearchTimer * 0.02f));
        char hudBuf[256];
        snprintf(hudBuf, sizeof(hudBuf), "REGION: GLOBAL  |  MATCHMAKER: ONLINE  |  PLAYERS: %d ACTIVE", mockPlayers);
        ui.drawText(hudBuf, SCREEN_W / 2, 75, 10, Color(150, 180, 200), "center");

        // Valorant sleek container panel
        ui.drawRectWithBorder(200, 100, 400, 385, Color(16, 20, 30, 240), Color(255, 70, 85, 100), 2);
        
        // Red top accent strip like Valorant menu
        drawRect(ren, 200, 100, 400, 5, Color(255, 70, 85));


        if (!netClient.loggedIn) {
            ui.drawText("로그인 및 회원가입 (LOGIN & REGISTER)", SCREEN_W / 2, 130, 13, Color(240, 240, 255), "center");

            // Server IP
            ui.drawText("서버 주소 (Server IP Address)", 250, 160, 9, Color(160, 180, 200), "left");
            Color ipBorder = (lobbyInputSel == 0) ? Color(255, 70, 85) : Color(60, 80, 110);
            ui.drawRectWithBorder(250, 173, 300, 32, (lobbyInputSel == 0) ? Color(30, 35, 55) : Color(18, 22, 34), ipBorder, (lobbyInputSel == 0) ? 2 : 1);
            ui.drawText(serverIP, 260, 182, 11, Color(255, 255, 255), "left");

            // Username
            ui.drawText("사용자 이름 (Username)", 250, 218, 9, Color(160, 180, 200), "left");
            Color userBorder = (lobbyInputSel == 1) ? Color(255, 70, 85) : Color(60, 80, 110);
            ui.drawRectWithBorder(250, 231, 300, 32, (lobbyInputSel == 1) ? Color(30, 35, 55) : Color(18, 22, 34), userBorder, (lobbyInputSel == 1) ? 2 : 1);
            ui.drawText(userTyped, 260, 240, 11, Color(255, 255, 255), "left");

            // Password
            ui.drawText("비밀번호 (Password)", 250, 276, 9, Color(160, 180, 200), "left");
            Color passBorder = (lobbyInputSel == 2) ? Color(255, 70, 85) : Color(60, 80, 110);
            ui.drawRectWithBorder(250, 289, 300, 32, (lobbyInputSel == 2) ? Color(30, 35, 55) : Color(18, 22, 34), passBorder, (lobbyInputSel == 2) ? 2 : 1);
            std::string maskedPass(passTyped.size(), '*');
            ui.drawText(maskedPass, 260, 298, 11, Color(255, 255, 255), "left");

            // Login Button
            bool loginHover = (mouseScreen.x >= 250 && mouseScreen.x <= 390 && mouseScreen.y >= 342 && mouseScreen.y <= 380);
            ui.drawRectWithBorder(250, 342, 140, 38, loginHover ? Color(255, 70, 85, 230) : Color(120, 30, 45, 200), loginHover ? Color(255, 255, 255) : Color(200, 50, 70), 1);
            ui.drawText("로그인 (Login)", 320, 355, 11, Color(255, 255, 255), "center");

            // Register Button
            bool regHover = (mouseScreen.x >= 410 && mouseScreen.x <= 550 && mouseScreen.y >= 342 && mouseScreen.y <= 380);
            ui.drawRectWithBorder(410, 342, 140, 38, regHover ? Color(55, 65, 110, 230) : Color(30, 38, 70, 200), regHover ? Color(150, 210, 255) : Color(70, 110, 180), 1);
            ui.drawText("회원가입 (Register)", 480, 355, 11, Color(220, 235, 255), "center");

            // Google Login Button
            bool googleHover = (mouseScreen.x >= 250 && mouseScreen.x <= 550 && mouseScreen.y >= 390 && mouseScreen.y <= 428);
            ui.drawRectWithBorder(250, 390, 300, 38, googleHover ? Color(240, 240, 240) : Color(255, 255, 255), googleHover ? Color(255, 255, 255) : Color(220, 220, 220), 1);
            ui.drawText("Google 계정으로 로그인 (Google Login)", 400, 403, 10, Color(60, 60, 60), "center");

            // Back Button
            bool backHover = (mouseScreen.x >= 250 && mouseScreen.x <= 550 && mouseScreen.y >= 438 && mouseScreen.y <= 476);
            ui.drawRectWithBorder(250, 438, 300, 38, backHover ? Color(40, 45, 55, 230) : Color(24, 28, 38, 200), backHover ? Color(200, 200, 220) : Color(100, 100, 120), 1);
            ui.drawText("돌아가기 (Go Back) [ESC]", 400, 451, 10, Color(210, 220, 230), "center");

            ui.drawText("Tab: 필드 이동 (Switch field)  |  타이핑 가능 (Click to type)", SCREEN_W / 2, 483, 9, Color(120, 140, 160), "center");
        } else {
            // Logged In Lobby
            if (mpSearching) {
                // Pulsing finding match header
                int blink = (int)(std::abs(std::sin(mpSearchTimer * 0.06f)) * 80 + 175);
                ui.drawText("FINDING MATCH", SCREEN_W / 2, 160, 20, Color((Uint8)blink, 50, 70), "center");
                
                int totalSecs = (int)(mpSearchTimer / 60.0f);
                int mins = totalSecs / 60;
                int secs = totalSecs % 60;
                char timeBuf[128];
                snprintf(timeBuf, sizeof(timeBuf), "매칭 대기 시간 (TIME ELAPSED) : %02d:%02d", mins, secs);
                ui.drawText(timeBuf, SCREEN_W / 2, 225, 12, Color(200, 220, 240), "center");

                ui.drawText("대기열의 다른 글로벌 플레이어와 연결 중...", SCREEN_W / 2, 260, 10, Color(140, 160, 180), "center");
                ui.drawText("Connecting to other players in the queue...", SCREEN_W / 2, 278, 10, Color(110, 130, 150), "center");

                // Cancel Match Button (Valorant themed red Cancel button)
                bool cancelHover = (mouseScreen.x >= 250 && mouseScreen.x <= 550 && mouseScreen.y >= 330 && mouseScreen.y <= 375);
                ui.drawRectWithBorder(250, 330, 300, 45, cancelHover ? Color(255, 70, 85, 230) : Color(150, 35, 45, 200), cancelHover ? Color(255, 255, 255) : Color(200, 50, 60), 1);
                ui.drawText("매칭 취소 (CANCEL MATCH) [ESC]", 400, 346, 12, Color(255, 235, 240), "center");
            } else {
                ui.drawText("WELCOME, " + netClient.loggedUser + "!", SCREEN_W / 2, 140, 15, Color(100, 255, 180), "center");

                // 1vs1 Button
                bool pvpHover = (mouseScreen.x >= 250 && mouseScreen.x <= 550 && mouseScreen.y >= 190 && mouseScreen.y <= 232);
                ui.drawRectWithBorder(250, 190, 300, 42, pvpHover ? Color(255, 70, 85) : Color(140, 30, 45), pvpHover ? Color(255, 255, 255) : Color(200, 50, 70), 1);
                ui.drawText("1vs1 아레나 대결 (1vs1 ARENA)", 400, 205, 12, Color(255, 255, 255), "center");

                // Coop Button
                bool coopHover = (mouseScreen.x >= 250 && mouseScreen.x <= 550 && mouseScreen.y >= 250 && mouseScreen.y <= 292);
                ui.drawRectWithBorder(250, 250, 300, 42, coopHover ? Color(35, 95, 75) : Color(20, 65, 50), coopHover ? Color(100, 255, 200) : Color(0, 180, 130), 1);
                ui.drawText("Co-op 공동 생존 (CO-OP SURVIVAL)", 400, 265, 12, Color(210, 255, 230), "center");

                // Logout Button
                bool logoutHover = (mouseScreen.x >= 250 && mouseScreen.x <= 550 && mouseScreen.y >= 325 && mouseScreen.y <= 363);
                ui.drawRectWithBorder(250, 325, 300, 38, logoutHover ? Color(60, 65, 75) : Color(35, 38, 45), logoutHover ? Color(200, 200, 220) : Color(120, 120, 130), 1);
                ui.drawText("로그아웃 (LOGOUT)", 400, 338, 11, Color(210, 220, 230), "center");

                // Back Button
                bool backHover = (mouseScreen.x >= 250 && mouseScreen.x <= 550 && mouseScreen.y >= 385 && mouseScreen.y <= 423);
                ui.drawRectWithBorder(250, 385, 300, 38, backHover ? Color(45, 50, 60) : Color(24, 28, 35), backHover ? Color(200, 200, 220) : Color(100, 100, 110), 1);
                ui.drawText("돌아가기 (GO BACK) [ESC]", 400, 398, 10, Color(200, 210, 220), "center");
            }
        }


        // Status Message at bottom
        if (!mpStatus.empty()) {
            Color statusCol = (mpStatus.find("❌") != std::string::npos || mpStatus.find("실패") != std::string::npos) ? Color(255, 100, 100) : Color(240, 220, 100);
            ui.drawText(mpStatus, SCREEN_W / 2, 485, 11, statusCol, "center");
        }
    }

    void handleMultiplayerLobbyEvent(const SDL_Event& e) {
        if (e.type == SDL_KEYDOWN) {
            if (e.key.keysym.scancode == SDL_SCANCODE_ESCAPE) {
                if (mpSearching) {
                    netClient.cancelMatchmaking(serverIP);
                    mpSearching = false;
                }
                SDL_StopTextInput();
                state = GameState::MENU;
                mpStatus = "";
                return;
            }

            if (!netClient.loggedIn) {
                if (e.key.keysym.scancode == SDL_SCANCODE_TAB) {
                    lobbyInputSel = (lobbyInputSel + 1) % 3;
                    return;
                }

                if (e.key.keysym.scancode == SDL_SCANCODE_RETURN) {
                    // Trigger login directly on Enter key
                    mpStatus = "로그인 중...";
                    if (netClient.loginUser(userTyped, passTyped, saveData, serverIP)) {
                        mpStatus = "로그인 성공!";
                        totalGold = saveData.gold;
                        totalDiamonds = saveData.diamonds;
                        SDL_StopTextInput();
                    } else {
                        mpStatus = "로그인 실패 (ID/PW 또는 서버 상태 확인)";
                    }
                    return;
                }

                if (e.key.keysym.scancode == SDL_SCANCODE_BACKSPACE) {
                    if (lobbyInputSel == 0 && !serverIP.empty()) {
                        serverIP.pop_back();
                    } else if (lobbyInputSel == 1 && !userTyped.empty()) {
                        userTyped.pop_back();
                    } else if (lobbyInputSel == 2 && !passTyped.empty()) {
                        passTyped.pop_back();
                    }
                    return;
                }
            }
        }

        // Text input handling
        if (e.type == SDL_TEXTINPUT && !netClient.loggedIn) {
            if (lobbyInputSel == 0) {
                serverIP += e.text.text;
            } else if (lobbyInputSel == 1) {
                userTyped += e.text.text;
            } else if (lobbyInputSel == 2) {
                passTyped += e.text.text;
            }
            return;
        }

        // Mouse click handling
        if (e.type == SDL_MOUSEBUTTONDOWN && e.button.button == SDL_BUTTON_LEFT) {
            int mx = e.button.x;
            int my = e.button.y;

            if (!netClient.loggedIn) {
                // Focus change by clicking on boxes
                if (mx >= 250 && mx <= 550 && my >= 185 && my <= 217) {
                    lobbyInputSel = 0;
                } else if (mx >= 250 && mx <= 550 && my >= 245 && my <= 277) {
                    lobbyInputSel = 1;
                } else if (mx >= 250 && mx <= 550 && my >= 305 && my <= 337) {
                    lobbyInputSel = 2;
                }
                // Buttons
                else if (mx >= 250 && mx <= 390 && my >= 342 && my <= 380) { // Login
                    mpStatus = "로그인 중...";
                    if (netClient.loginUser(userTyped, passTyped, saveData, serverIP)) {
                        mpStatus = "로그인 성공!";
                        totalGold = saveData.gold;
                        totalDiamonds = saveData.diamonds;
                        SDL_StopTextInput();
                    } else {
                        mpStatus = "로그인 실패 (ID/PW 또는 서버 상태 확인)";
                    }
                }
                else if (mx >= 410 && mx <= 550 && my >= 342 && my <= 380) { // Register
                    mpStatus = "회원가입 진행 중...";
                    if (netClient.registerUser(userTyped, passTyped, serverIP)) {
                        mpStatus = "회원가입 성공! 이제 로그인 해주세요.";
                    } else {
                        mpStatus = "회원가입 실패 (이미 존재하는 ID 등)";
                    }
                }
                else if (mx >= 250 && mx <= 550 && my >= 390 && my <= 428) { // Google Login
                    mpStatus = "구글 인증 대기 중 (브라우저를 확인하세요)...";
                    if (netClient.loginGoogle(saveData)) {
                        mpStatus = "구글 로그인 성공!";
                        totalGold = saveData.gold;
                        totalDiamonds = saveData.diamonds;
                        SDL_StopTextInput();
                    } else {
                        mpStatus = "❌ 구글 로그인 실패 또는 취소됨";
                    }
                }
                else if (mx >= 250 && mx <= 550 && my >= 438 && my <= 476) { // Back
                    SDL_StopTextInput();
                    state = GameState::MENU;
                    mpStatus = "";
                }
            } else {
                if (mpSearching) {
                    if (mx >= 250 && mx <= 550 && my >= 320 && my <= 365) { // Cancel Match
                        netClient.cancelMatchmaking(serverIP);
                        mpSearching = false;
                        mpStatus = "매치메이킹 취소됨";
                        SDL_StartTextInput(); // Restart input context just in case
                    }
                } else {
                    if (mx >= 250 && mx <= 550 && my >= 190 && my <= 232) { // 1vs1
                        mpStatus = "1vs1 아레나 매칭 큐에 진입 중...";
                        if (netClient.startMatchmaking("1v1", serverIP)) {
                            mpSearching = true;
                            mpSearchTimer = 0.0f;
                            mpMode = "1v1";
                        } else {
                            mpStatus = "❌ 매칭 진입 실패 (서버 연결 확인)";
                        }
                    }
                    else if (mx >= 250 && mx <= 550 && my >= 250 && my <= 292) { // Coop
                        mpStatus = "Co-op 협동 생존 매칭 큐에 진입 중...";
                        if (netClient.startMatchmaking("coop", serverIP)) {
                            mpSearching = true;
                            mpSearchTimer = 0.0f;
                            mpMode = "coop";
                        } else {
                            mpStatus = "❌ 매칭 진입 실패 (서버 연결 확인)";
                        }
                    }
                    else if (mx >= 250 && mx <= 550 && my >= 325 && my <= 363) { // Logout
                        netClient.cleanup();
                        netClient.loggedIn = false;
                        netClient.loggedUser = "";
                        netClient.clearSession();
                        mpStatus = "로그아웃되었습니다.";
                        SDL_StartTextInput();
                    }
                    else if (mx >= 250 && mx <= 550 && my >= 385 && my <= 423) { // Back
                        state = GameState::MENU;
                        mpStatus = "";
                    }
                }
            }
        }
    }
};

