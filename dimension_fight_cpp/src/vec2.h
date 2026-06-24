#pragma once
#include <cmath>
#include <algorithm>

struct Vec2 {
    float x = 0, y = 0;
    Vec2() = default;
    Vec2(float x, float y) : x(x), y(y) {}

    Vec2 operator+(const Vec2& o) const { return {x + o.x, y + o.y}; }
    Vec2 operator-(const Vec2& o) const { return {x - o.x, y - o.y}; }
    Vec2 operator*(float s) const { return {x * s, y * s}; }
    Vec2 operator/(float s) const { return {x / s, y / s}; }
    Vec2& operator+=(const Vec2& o) { x += o.x; y += o.y; return *this; }
    Vec2& operator-=(const Vec2& o) { x -= o.x; y -= o.y; return *this; }
    Vec2& operator*=(float s) { x *= s; y *= s; return *this; }

    float length() const { return std::sqrt(x * x + y * y); }
    float lengthSq() const { return x * x + y * y; }
    float dist(const Vec2& o) const { return (*this - o).length(); }
    float distSq(const Vec2& o) const { return (*this - o).lengthSq(); }

    Vec2 normalized() const {
        float l = length();
        return l > 0.0001f ? Vec2{x / l, y / l} : Vec2{0, 0};
    }
    float angle() const { return std::atan2(y, x); }
    float angleDeg() const { return angle() * 180.0f / 3.14159265f; }

    static Vec2 fromAngle(float rad, float len = 1.0f) {
        return {std::cos(rad) * len, std::sin(rad) * len};
    }
    static Vec2 fromAngleDeg(float deg, float len = 1.0f) {
        return fromAngle(deg * 3.14159265f / 180.0f, len);
    }
    static Vec2 lerp(const Vec2& a, const Vec2& b, float t) {
        return a + (b - a) * t;
    }
};
