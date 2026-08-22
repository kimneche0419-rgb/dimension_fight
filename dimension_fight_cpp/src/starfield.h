#pragma once
#include "vec2.h"
#include "utils.h"
#include "data.h"
#include <vector>

class StarField {
    struct Star { float x, y; };
    struct Layer { std::vector<Star> stars; float parallax; int size; int bright; };
    struct Nebula { float x, y; int size; Color color; float parallax; };

    std::vector<Layer> layers;
    std::vector<Nebula> nebulae;

public:
    StarField(int count = 180) {
        for (int l = 0; l < 3; l++) {
            Layer layer;
            layer.parallax = 0.15f + l * 0.25f;
            layer.size = l + 1;
            layer.bright = 70 + l * 55;
            for (int i = 0; i < count / 3; i++) {
                layer.stars.push_back({randf(0, 3000), randf(0, 3000)});
            }
            layers.push_back(layer);
        }
        for (int i = 0; i < 12; i++) {
            nebulae.push_back({
                randf(0, 3000), randf(0, 3000),
                randi(200, 500),
                Color(randi(20,60), randi(0,30), randi(40,100), 40),
                0.1f
            });
        }
    }

    void draw(SDL_Renderer* ren, Vec2 camOff, Dimension dim, bool abyss = false) {
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);

        // Nebulae
        for (auto& n : nebulae) {
            float px = std::fmod(n.x - camOff.x * n.parallax, 3000.0f);
            float py = std::fmod(n.y - camOff.y * n.parallax, 3000.0f);
            if (px < 0) px += 3000;
            if (py < 0) py += 3000;
            for (int ox = -3000; ox <= 3000; ox += 3000) {
                for (int oy = -3000; oy <= 3000; oy += 3000) {
                    int fx = (int)(px + ox), fy = (int)(py + oy);
                    if (fx >= -100 && fx <= SCREEN_W + 100 && fy >= -100 && fy <= SCREEN_H + 100) {
                        drawFilledCircle(ren, fx, fy, n.size / 3, n.color);
                    }
                }
            }
        }

        // Stars
        for (auto& layer : layers) {
            for (auto& s : layer.stars) {
                float px = std::fmod(s.x - camOff.x * layer.parallax, 3000.0f);
                float py = std::fmod(s.y - camOff.y * layer.parallax, 3000.0f);
                if (px < 0) px += 3000;
                if (py < 0) py += 3000;
                for (int ox = -3000; ox <= 3000; ox += 3000) {
                    for (int oy = -3000; oy <= 3000; oy += 3000) {
                        int fx = (int)(px + ox), fy = (int)(py + oy);
                        if (fx >= 0 && fx <= SCREEN_W && fy >= 0 && fy <= SCREEN_H) {
                            int b = layer.bright;
                            Color col;
                            if (abyss) col = Color(0, b/2, b);
                            else if (dim == Dimension::VOID_DIM) col = Color(b, b/3, b);
                            else col = Color(b, b, std::min(255, b+30));
                            drawFilledCircle(ren, fx, fy, layer.size, col);
                        }
                    }
                }
            }
        }
    }
};
