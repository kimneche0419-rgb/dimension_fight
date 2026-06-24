#pragma once
#include "vec2.h"
#include "utils.h"

class Camera {
public:
    Vec2 offset;
    float smooth = 0.14f;
    int shakeTimer = 0;
    float shakeAmount = 0;

    void update(Vec2 playerPos) {
        Vec2 target = playerPos - Vec2(SCREEN_W / 2.0f, SCREEN_H / 2.0f);
        offset = Vec2::lerp(offset, target, smooth);

        if (shakeTimer > 0) {
            shakeTimer--;
        }
    }

    void shake(float amount = 8.0f, int frames = 10) {
        shakeAmount = amount;
        shakeTimer = frames;
    }

    Vec2 getShake() const {
        if (shakeTimer > 0) {
            return Vec2(randf(-shakeAmount, shakeAmount),
                       randf(-shakeAmount, shakeAmount));
        }
        return Vec2(0, 0);
    }

    Vec2 worldToScreen(Vec2 worldPos) const {
        return worldPos - offset;
    }

    bool isVisible(Vec2 worldPos, float margin = 50) const {
        Vec2 sp = worldToScreen(worldPos);
        return sp.x >= -margin && sp.x <= SCREEN_W + margin &&
               sp.y >= -margin && sp.y <= SCREEN_H + margin;
    }
};
