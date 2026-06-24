#pragma once
#include <SDL.h>
#include <SDL_mixer.h>
#include <string>
#include <map>

class SoundManager {
    std::map<std::string, Mix_Chunk*> sounds;
    std::string currentBGM;
    bool enabled = false;

public:
    ~SoundManager() {
        for (auto& [k, v] : sounds) {
            if (v) Mix_FreeChunk(v);
        }
        Mix_CloseAudio();
    }

    bool init() {
        if (Mix_OpenAudio(22050, MIX_DEFAULT_FORMAT, 2, 1024) < 0) {
            SDL_Log("Mix_OpenAudio failed: %s", Mix_GetError());
            return false;
        }
        Mix_AllocateChannels(16);
        enabled = true;

        // Load SFX
        loadSound("shoot",     "assets/sounds/sfx_shoot.wav");
        loadSound("explosion", "assets/sounds/sfx_explosion.wav");
        loadSound("hit",       "assets/sounds/sfx_hit.wav");
        loadSound("levelup",   "assets/sounds/sfx_levelup.wav");
        loadSound("shift",     "assets/sounds/sfx_shift.wav");
        loadSound("purchase",  "assets/sounds/sfx_purchase.wav");

        return true;
    }

    void loadSound(const std::string& key, const std::string& path) {
        Mix_Chunk* chunk = Mix_LoadWAV(path.c_str());
        if (chunk) {
            sounds[key] = chunk;
        } else {
            SDL_Log("Failed to load sound %s: %s", path.c_str(), Mix_GetError());
        }
    }

    void playSFX(const std::string& key) {
        if (!enabled) return;
        auto it = sounds.find(key);
        if (it != sounds.end() && it->second) {
            Mix_PlayChannel(-1, it->second, 0);
        }
    }

    void playBGM(const std::string& name) {
        if (!enabled || currentBGM == name) return;
        std::string path = "assets/music/bgm_" + name + ".wav";
        Mix_Music* music = Mix_LoadMUS(path.c_str());
        if (music) {
            Mix_PlayMusic(music, -1);
            currentBGM = name;
        }
    }

    void stopBGM() {
        Mix_HaltMusic();
        currentBGM = "";
    }

    void updateBGM(const std::string& state, bool hasBoss = false) {
        if (state == "MENU" || state == "SHOP") {
            playBGM("menu");
        } else if (state == "WIN") {
            playBGM("victory");
        } else if (state == "DEATH") {
            playBGM("gameover");
        } else if (state == "PLAYING") {
            if (hasBoss) playBGM("boss");
            else playBGM("chapter_1");
        }
    }
};
