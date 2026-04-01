import pygame
from pygame.math import Vector2
import random
import math

# ─────────────────────────────────────────
#  GLOBAL SETTINGS  (런타임 감도/물리 설정)
# ─────────────────────────────────────────
class GameSettings:
    """모든 이동·물리 관련 설정을 담는 싱글턴"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_defaults()
        return cls._instance

    def _init_defaults(self):
        # SHIP 모드
        self.ship_accel        = 0.38   # 선박 가속력  (0.10 ~ 1.0)
        self.ship_max_speed    = 5.5    # 선박 최대속도 (2.0 ~ 12.0)
        self.ship_friction     = 0.82   # 선박 마찰배율 (0.50 ~ 0.99)  값 낮을수록 빨리 멈춤
        self.ship_rotate_speed = 0.18   # 마우스 추종 회전속도 (0.05 ~ 0.40)

        # HUMAN 모드
        self.human_accel       = 0.9    # 인간 가속력  (0.20 ~ 2.0)
        self.human_base_speed  = 1.5    # 인간 기본속도 (0.5 ~ 4.0)

        # DASH
        self.dash_speed        = 20     # 대쉬 거리속도 (8 ~ 40)
        self.dash_frames       = 10     # 대쉬 지속 프레임 (5 ~ 20)
        self.dash_cooldown     = 50     # 대쉬 쿨타임 프레임 (20 ~ 120)

        # 카메라
        self.camera_smooth     = 0.12   # 카메라 부드러움 (0.05 ~ 0.40) 높을수록 빠르게 따라감

    LABELS = {
        "ship_accel":        ("선박 가속력",       0.10, 1.00, 0.05),
        "ship_max_speed":    ("선박 최대속도",      2.0,  12.0, 0.5),
        "ship_friction":     ("선박 마찰(관성)",   0.50, 0.99, 0.02),
        "ship_rotate_speed": ("마우스 회전감도",   0.05, 0.40, 0.01),
        "human_accel":       ("인간 가속력",       0.20, 2.00, 0.10),
        "human_base_speed":  ("인간 기본속도",     0.50, 4.00, 0.25),
        "dash_speed":        ("대쉬 속도",         8,    40,   2),
        "dash_frames":       ("대쉬 지속(프레임)", 5,    20,   1),
        "dash_cooldown":     ("대쉬 쿨타임(프레임)",20,  120,  5),
        "camera_smooth":     ("카메라 반응속도",   0.05, 0.40, 0.01),
    }

    KEYS_ORDER = [
        "ship_accel","ship_max_speed","ship_friction","ship_rotate_speed",
        "human_accel","human_base_speed",
        "dash_speed","dash_frames","dash_cooldown",
        "camera_smooth",
    ]

    def reset_defaults(self):
        self._init_defaults()


# 전역 싱글턴
SETTINGS = GameSettings()

# ─────────────────────────────────────────
#  WEAPONS
# ─────────────────────────────────────────
WEAPONS = {
    "laser":      {"name":"Laser",     "cooldown":18,"speed":14,"dmg":1, "color_p":(0,255,255),  "color_v":(255,0,255),  "size":5, "spread":0,  "count":1},
    "shotgun":    {"name":"Shotgun",   "cooldown":38,"speed":10,"dmg":2, "color_p":(255,200,0),  "color_v":(255,100,0),  "size":4, "spread":22, "count":6},
    "sniper":     {"name":"Sniper",    "cooldown":55,"speed":22,"dmg":4, "color_p":(200,255,200),"color_v":(100,255,100),"size":3, "spread":0,  "count":1},
    "gatling":    {"name":"Gatling",   "cooldown":5, "speed":11,"dmg":1, "color_p":(255,150,50), "color_v":(200,50,255), "size":4, "spread":10, "count":1},
    "rocket":     {"name":"Rocket",   "cooldown":75,"speed":8, "dmg":6, "color_p":(255,80,80),  "color_v":(180,0,180),  "size":8, "spread":0,  "count":1},
    "robot_arm":  {"name":"RobotArm", "cooldown":14,"speed":12,"dmg":2, "color_p":(100,200,255),"color_v":(200,100,255),"size":6, "spread":5,  "count":2},
    "plasma":     {"name":"Plasma",   "cooldown":28,"speed":9, "dmg":3, "color_p":(180,0,255),  "color_v":(0,255,180),  "size":9, "spread":5,  "count":3},
    "railgun":    {"name":"Railgun",  "cooldown":90,"speed":28,"dmg":8, "color_p":(255,255,0),  "color_v":(255,100,0),  "size":4, "spread":0,  "count":1},
    "void_cannon":{"name":"VoidCann", "cooldown":45,"speed":7, "dmg":5, "color_p":(80,0,180),   "color_v":(0,220,255),  "size":12,"spread":0,  "count":1},
    "abyss_beam": {"name":"AbysBeam", "cooldown":8, "speed":16,"dmg":2, "color_p":(0,80,200),   "color_v":(200,0,100),  "size":5, "spread":2,  "count":2},
}
WEAPON_ORDER        = ["laser","shotgun","sniper","gatling","rocket","robot_arm","plasma","railgun","void_cannon","abyss_beam"]
WEAPON_UNLOCK_LEVEL = [1,      3,        5,       8,        12,      16,         20,      25,       30,           35]

# ─────────────────────────────────────────
#  SHIP FORMS  (우주선 변형)
# ─────────────────────────────────────────
# ─────────────────────────────────────────
#  SHIP COLOR PALETTES  (플레이어 색상 선택)
# ─────────────────────────────────────────
SHIP_COLORS = [
    {"name": "시안",      "key": "cyan",    "color_p": (0,255,255),   "color_v": (255,0,255)},
    {"name": "불꽃 적",   "key": "red",     "color_p": (255,80,80),   "color_v": (255,200,0)},
    {"name": "에메랄드",  "key": "emerald", "color_p": (0,255,120),   "color_v": (0,180,255)},
    {"name": "황금",      "key": "gold",    "color_p": (255,220,50),  "color_v": (255,100,0)},
    {"name": "보라",      "key": "violet",  "color_p": (200,80,255),  "color_v": (100,255,200)},
    {"name": "백색광",    "key": "white",   "color_p": (220,235,255), "color_v": (255,200,100)},
    {"name": "심해 청",   "key": "abyss",   "color_p": (0,120,255),   "color_v": (0,255,200)},
    {"name": "진홍",      "key": "crimson", "color_p": (220,0,60),    "color_v": (255,140,200)},
]

SHIP_FORMS = {
    "fighter": {
        "name": "전투기 (Fighter)",
        "color_p": (0,255,255), "color_v": (255,0,255),
        "desc": "기본형 · 균형 잡힌 성능",
        "speed_mult": 1.0, "dmg_mult": 1.0, "cd_mult": 1.0,
        # 폴리곤 포인트 (36x36 기준)
        "poly": [(18,0),(36,36),(18,26),(0,36)],
        "engine_pos": [(18,30)], "engine_r": 4,
    },
    "cruiser": {
        "name": "순양함 (Cruiser)",
        "color_p": (80,200,255), "color_v": (200,80,255),
        "desc": "넓은 날개 · 탄 2발 추가",
        "speed_mult": 0.8, "dmg_mult": 1.0, "cd_mult": 0.9,
        "poly": [(18,0),(36,20),(30,36),(18,28),(6,36),(0,20)],
        "engine_pos": [(8,32),(28,32)], "engine_r": 3,
    },
    "stealth": {
        "name": "스텔스 (Stealth)",
        "color_p": (120,120,180), "color_v": (180,60,255),
        "desc": "얇고 날렵 · 대쉬 쿨타임 -30%",
        "speed_mult": 1.3, "dmg_mult": 0.8, "cd_mult": 1.1,
        "poly": [(18,0),(28,36),(18,22),(8,36)],
        "engine_pos": [(18,34)], "engine_r": 3,
        "dash_mult": 0.7,
    },
    "dreadnought": {
        "name": "드레드노트 (Dreadnought)",
        "color_p": (255,80,80), "color_v": (255,160,0),
        "desc": "무거운 전함 · 데미지 ×2 · 느림",
        "speed_mult": 0.6, "dmg_mult": 2.0, "cd_mult": 0.8,
        "poly": [(18,0),(36,12),(36,30),(24,36),(12,36),(0,30),(0,12)],
        "engine_pos": [(10,34),(18,36),(26,34)], "engine_r": 4,
    },
    "abyss_ship": {
        "name": "심해함 (Abyss Ship)",
        "color_p": (0,80,180), "color_v": (0,200,255),
        "desc": "심해 특화 · 독성 면역 · 특수 쉴드",
        "speed_mult": 0.9, "dmg_mult": 1.2, "cd_mult": 1.0,
        "poly": [(18,2),(34,16),(28,36),(18,30),(8,36),(2,16)],
        "engine_pos": [(18,32)], "engine_r": 5,
        "toxic_immune": True,
    },
    "phantom": {
        "name": "팬텀 (Phantom)",
        "color_p": (200,200,255), "color_v": (255,255,100),
        "desc": "차원 에너지 흡수 · 보이드 데미지 ×1.5",
        "speed_mult": 1.1, "dmg_mult": 1.0, "cd_mult": 1.0,
        "poly": [(18,0),(30,12),(36,28),(18,36),(0,28),(6,12)],
        "engine_pos": [(18,34)], "engine_r": 4,
        "void_bonus": 1.5,
    },
}

# ─────────────────────────────────────────
#  PARTICLE
# ─────────────────────────────────────────
class Particle:
    def __init__(self, pos, vel, color, life, size=3):
        self.pos      = Vector2(pos)
        self.vel      = Vector2(vel)
        self.color    = list(color)[:3]
        self.life     = life
        self.max_life = life
        self.size     = size

    def update(self):
        self.pos += self.vel
        self.vel *= 0.93
        self.life -= 1
        return self.life > 0

    def draw(self, surface, camera_offset):
        alpha = int(255 * self.life / self.max_life)
        r = max(1, int(self.size * self.life / self.max_life))
        sx = int(self.pos.x - camera_offset.x)
        sy = int(self.pos.y - camera_offset.y)
        if -20 <= sx <= 820 and -20 <= sy <= 620:
            try:
                surf = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
                col  = tuple(min(255, max(0, int(c))) for c in self.color)
                pygame.draw.circle(surf, (*col, alpha), (r+1,r+1), r)
                surface.blit(surf, (sx-r-1, sy-r-1))
            except Exception:
                pass


# ─────────────────────────────────────────
#  BLACKHOLE  (차원 이동 시 확률 생성)
# ─────────────────────────────────────────
class Blackhole:
    """블랙홀 — 가까운 적/탄 흡수, 플레이어 흡인, 60초 후 소멸
       소멸 시 '심해 차원(ABYSS)' 1분간 활성화 이벤트 발생"""
    def __init__(self, world_pos):
        self.world_pos  = Vector2(world_pos)
        self.radius     = 0          # 성장 반경
        self.max_radius = 90
        self.age        = 0
        self.max_age    = 3600       # 60초
        self.alive      = True
        self.spin_angle = 0
        self.pull_range = 350        # 인력 범위
        self.pull_force = 0.18

    def update(self):
        self.age += 1
        self.spin_angle = (self.spin_angle + 3) % 360
        # 성장 → 유지 → 축소
        if self.age < 120:
            self.radius = int(self.max_radius * self.age / 120)
        elif self.age > self.max_age - 120:
            t = (self.max_age - self.age) / 120
            self.radius = max(1, int(self.max_radius * t))
        else:
            self.radius = self.max_radius
        if self.age >= self.max_age:
            self.alive = False

    def apply_pull(self, world_pos, vel):
        """인력 계산 반환 (pos 인수, vel 수정)"""
        d = self.world_pos - world_pos
        dist = d.length()
        if 0 < dist < self.pull_range:
            force = self.pull_force * (1 - dist / self.pull_range) * 2
            return d.normalize() * force
        return Vector2(0, 0)

    def draw(self, surface, camera_offset, frame):
        cx = int(self.world_pos.x - camera_offset.x)
        cy = int(self.world_pos.y - camera_offset.y)
        if not (-120 <= cx <= 920 and -120 <= cy <= 720):
            return
        # 외곽 인력 링 (점선)
        for i in range(8):
            a = self.spin_angle + i * 45
            lx = cx + int(math.cos(math.radians(a)) * self.pull_range * 0.7)
            ly = cy + int(math.sin(math.radians(a)) * self.pull_range * 0.7)
            alpha = int(60 * (1 - self.age % 30 / 30))
            try:
                s = pygame.Surface((6,6), pygame.SRCALPHA)
                pygame.draw.circle(s, (180,0,255,alpha), (3,3), 3)
                surface.blit(s, (lx-3, ly-3))
            except Exception:
                pass
        # 외곽 링들
        for ri, (rad, alpha, col) in enumerate([
            (self.radius+30, 60,  (100,0,200)),
            (self.radius+15, 100, (160,0,255)),
            (self.radius,    180, (200,50,255)),
        ]):
            try:
                s = pygame.Surface((rad*2+4, rad*2+4), pygame.SRCALPHA)
                pygame.draw.circle(s, (*col, alpha), (rad+2, rad+2), rad, 3)
                surface.blit(s, (cx-rad-2, cy-rad-2))
            except Exception:
                pass
        # 코어 (검은 원)
        r = max(1, self.radius)
        try:
            s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(s, (0,0,0,240), (r+1,r+1), r)
            # 중심 빛
            pygame.draw.circle(s, (255,100,255,200), (r+1,r+1), max(1,r//5))
            surface.blit(s, (cx-r-1, cy-r-1))
        except Exception:
            pass
        # 나선 팔
        for arm in range(3):
            base_angle = self.spin_angle * 2 + arm * 120
            for step in range(20):
                t   = step / 20
                rad = (self.radius + 10) * (0.2 + t * 0.8)
                ang = base_angle + t * 180
                px  = cx + int(math.cos(math.radians(ang)) * rad)
                py  = cy + int(math.sin(math.radians(ang)) * rad)
                alpha = int(180 * (1 - t))
                try:
                    ps = pygame.Surface((4,4), pygame.SRCALPHA)
                    pygame.draw.circle(ps, (200, int(50+80*t), 255, alpha), (2,2), 2)
                    surface.blit(ps, (px-2, py-2))
                except Exception:
                    pass
        # 수명 표시
        if self.age < self.max_age - 60:
            remain = (self.max_age - self.age) // 60
            try:
                f = pygame.font.SysFont(None, 16)
                txt = f.render(f"{remain}s", True, (200,100,255))
                surface.blit(txt, (cx - 10, cy - self.radius - 18))
            except Exception:
                pass


# ─────────────────────────────────────────
#  PICKUP ITEM
# ─────────────────────────────────────────
ITEM_DATA = {
    "hp":        {"color": (0,255,80),    "label": "HP+30"},
    "shield":    {"color": (0,180,255),   "label": "SHIELD"},
    "speed":     {"color": (255,100,255), "label": "SPD"},
    "ammo":      {"color": (255,140,0),   "label": "AMMO"},
    "ship_form": {"color": (255,220,50),  "label": "FORM"},
}

class PickupItem(pygame.sprite.Sprite):
    def __init__(self, world_pos, itype="hp"):
        super().__init__()
        self.world_pos = Vector2(world_pos)
        self.itype = itype
        self.age   = 0
        sz = 18
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        c = ITEM_DATA.get(itype, ITEM_DATA["hp"])["color"]
        if itype == "ship_form":
            pygame.draw.polygon(self.image, c, [(9,0),(18,10),(14,18),(4,18),(0,10)])
            pygame.draw.circle(self.image, (255,255,255), (9,9), 4, 1)
        else:
            pygame.draw.rect(self.image, c, (0,0,sz,sz), border_radius=5)
            pygame.draw.rect(self.image, (255,255,255), (0,0,sz,sz), 1, border_radius=5)
        self.rect = self.image.get_rect()

    def update_screen_pos(self, camera_offset):
        self.rect.center = (int(self.world_pos.x - camera_offset.x),
                            int(self.world_pos.y - camera_offset.y))

    def update(self):
        self.age += 1
        return self.age < 700


# ─────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.base_image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.image      = self.base_image
        self.rect       = self.image.get_rect(center=(400,300))
        self.world_pos  = Vector2(pos)
        self.pos        = self.world_pos
        self.vel        = Vector2(0,0)
        self.angle      = 0
        self.dimension  = "PHYSICAL"
        self.health     = 100
        self.max_health = 100
        self.shield     = 0
        self.max_shield = 60
        self.invincible = 0
        self.level      = 1
        self.xp         = 0
        self.xp_to_next = 10
        self.timer      = 0
        self.mode       = "HUMAN"
        self.score      = 0
        self.kill_count = 0

        self.combo       = 0
        self.combo_timer = 0
        self.max_combo   = 0

        self.dash_cd     = 0
        self.dash_timer  = 0
        self.dash_dir    = Vector2(0,0)
        self.DASH_SPEED  = 20
        self.DASH_FRAMES = 10
        self.DASH_CD     = 50

        self.speed_boost = 0
        self.weapon_key  = "laser"
        self.unlocked_weapons = ["laser"]
        self._cd_bonus   = 0

        # 우주선 변형
        self.ship_form     = "fighter"
        self.form_morph_t  = 0     # 변형 애니메이션 0→1
        self.form_prev     = "fighter"
        self.unlocked_forms = ["fighter"]

        # 우주선 색상 커스텀
        self.ship_color_key = "cyan"   # SHIP_COLORS key

        # 심해 차원 버프
        self.abyss_mode = False   # ABYSS 차원 활성 시

    @property
    def weapon(self):
        return WEAPONS[self.weapon_key]

    @property
    def weapon_cooldown(self):
        form  = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        cd_m  = form.get("cd_mult", 1.0)
        return max(3, int(self.weapon["cooldown"] * cd_m) - self._cd_bonus * 2)

    def get_dmg_mult(self):
        form = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        m = form.get("dmg_mult", 1.0)
        if self.abyss_mode:
            m *= 1.3
        if self.dimension == "VOID":
            m *= form.get("void_bonus", 1.0)
        return m

    def get_speed_mult(self):
        form = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        return form.get("speed_mult", 1.0)

    def get_dash_cd_mult(self):
        form = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        return form.get("dash_mult", 1.0)

    def check_unlock(self):
        newly = None
        for i, lv in enumerate(WEAPON_UNLOCK_LEVEL):
            wk = WEAPON_ORDER[i]
            if self.level >= lv and wk not in self.unlocked_weapons:
                self.unlocked_weapons.append(wk)
                newly = wk
        return newly

    def switch_weapon(self, direction=1):
        idx = WEAPON_ORDER.index(self.weapon_key)
        for _ in range(len(WEAPON_ORDER)):
            idx = (idx + direction) % len(WEAPON_ORDER)
            if WEAPON_ORDER[idx] in self.unlocked_weapons:
                self.weapon_key = WEAPON_ORDER[idx]
                break

    def morph_to(self, form_key):
        if form_key not in SHIP_FORMS:
            return
        if form_key == self.ship_form:
            return
        self.form_prev   = self.ship_form
        self.ship_form   = form_key
        self.form_morph_t = 0

    def try_dash(self, keys):
        cd = int(SETTINGS.dash_cooldown * self.get_dash_cd_mult())
        if self.dash_cd > 0:
            return False
        move = Vector2(0,0)
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: move.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move.x += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: move.y -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: move.y += 1
        if move.length() == 0:
            move = Vector2(math.cos(math.radians(self.angle+90)),
                           -math.sin(math.radians(self.angle+90)))
        self.DASH_SPEED  = SETTINGS.dash_speed
        self.DASH_FRAMES = SETTINGS.dash_frames
        self.dash_dir    = move.normalize()
        self.dash_timer  = self.DASH_FRAMES
        self.dash_cd     = cd
        self.invincible  = max(self.invincible, self.DASH_FRAMES + 5)
        return True

    def update(self, keys, current_friction, mode, mouse_pos=None):
        self.mode = mode
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            if self.combo > 0:
                self.combo = max(0, self.combo - 1)
        if self.dash_cd > 0:
            self.dash_cd -= 1
        if self.speed_boost > 0:
            self.speed_boost -= 1
        if self.form_morph_t < 1.0:
            self.form_morph_t = min(1.0, self.form_morph_t + 0.06)

        if mode == "SHIP":
            self._update_ship(keys, current_friction, mouse_pos)
        else:
            self._update_human(keys, current_friction, mouse_pos)

        if self.dash_timer > 0:
            self.world_pos += self.dash_dir * self.DASH_SPEED
            self.dash_timer -= 1

        self.pos = self.world_pos
        self.rect.center = (400, 300)

    def _update_human(self, keys, friction, mouse_pos):
        base = SETTINGS.human_base_speed
        spd = ((base * 1.46) if self.speed_boost > 0 else base) * self.get_speed_mult()
        move = Vector2(0,0)
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: move.x -= spd
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move.x += spd
        if keys[pygame.K_UP]    or keys[pygame.K_w]: move.y -= spd
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: move.y += spd
        if move.length() > 0:
            self.vel += move.normalize() * SETTINGS.human_accel
        self.vel *= (1 + friction * 2)
        self.world_pos += self.vel
        if mouse_pos:
            diff = Vector2(mouse_pos) - Vector2(400,300)
            if diff.length() > 0:
                self.angle = math.degrees(math.atan2(-diff.y, diff.x)) - 90
        self._redraw()

    def _update_ship(self, keys, friction, mouse_pos):
        if mouse_pos:
            diff = Vector2(mouse_pos) - Vector2(400,300)
            if diff.length() > 1:
                target = math.degrees(math.atan2(-diff.y, diff.x)) - 90
                da = (target - self.angle + 180) % 360 - 180
                self.angle += da * SETTINGS.ship_rotate_speed
        spd = (1.6 if self.speed_boost > 0 else 1.0) * self.get_speed_mult()
        move = Vector2(0,0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:    move.y -= spd
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  move.y += spd
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  move.x -= spd
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move.x += spd
        if move.length() > 0:
            self.vel += move.normalize() * SETTINGS.ship_accel
        self.vel *= (1 + friction) * SETTINGS.ship_friction
        # 최대 속도 캡
        max_spd = SETTINGS.ship_max_speed * self.get_speed_mult()
        if self.vel.length() > max_spd:
            self.vel.scale_to_length(max_spd)
        self.world_pos += self.vel
        self._redraw()

    def _redraw(self):
        self.base_image.fill((0,0,0,0))
        form = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        t    = self.form_morph_t

        # 커스텀 색상 팔레트 적용
        color_data = next((c for c in SHIP_COLORS if c["key"]==self.ship_color_key), SHIP_COLORS[0])

        if self.dash_timer > 0:
            color = (255,255,255)
        elif self.abyss_mode:
            color = (0,200,255)
        else:
            color = color_data["color_p"] if self.dimension=="PHYSICAL" else color_data["color_v"]

        if self.mode == "SHIP":
            # 변형 보간 (이전 폼 → 현재 폼 선형 보간)
            poly_curr = form["poly"]
            poly_prev = SHIP_FORMS.get(self.form_prev, form)["poly"]

            def lerp_poly(pa, pb, t):
                # 두 폴리곤 길이 맞춤 (짧은 쪽 마지막 점 반복)
                n = max(len(pa), len(pb))
                def ext(p, n):
                    return p + [p[-1]]*(n-len(p))
                pa2 = ext(pa, n); pb2 = ext(pb, n)
                return [(int(a[0]+(b[0]-a[0])*t), int(a[1]+(b[1]-a[1])*t))
                        for a, b in zip(pa2, pb2)]

            poly = lerp_poly(poly_prev, poly_curr, t)
            if len(poly) >= 3:
                pygame.draw.polygon(self.base_image, color, poly)
                pygame.draw.polygon(self.base_image, (255,255,255), poly, 1)

            # 엔진 불꽃
            eng_col = (0,200,255) if self.abyss_mode else (255,150,50)
            for ep in form["engine_pos"]:
                er = form["engine_r"]
                pygame.draw.circle(self.base_image, eng_col, ep, er)
                if self.speed_boost > 0:
                    pygame.draw.circle(self.base_image, (255,255,200), ep, er+2, 1)

            # 드레드노트 특수 — 측면 포
            if self.ship_form == "dreadnought":
                pygame.draw.rect(self.base_image, (200,50,50), (0,10,6,8))
                pygame.draw.rect(self.base_image, (200,50,50), (34,10,6,8))

            # 심해함 특수 — 에너지 링
            if self.ship_form == "abyss_ship":
                pygame.draw.circle(self.base_image, (0,150,255), (20,20), 18, 1)

            # 팬텀 특수 — 차원 아우라
            if self.ship_form == "phantom":
                aura_col = (200,200,255) if self.dimension=="PHYSICAL" else (255,220,0)
                pygame.draw.circle(self.base_image, aura_col, (20,20), 19, 1)

        else:  # HUMAN 모드
            color_h = (0,255,255) if self.dimension=="PHYSICAL" else (255,0,255)
            if self.abyss_mode: color_h = (0,200,255)
            pygame.draw.circle(self.base_image, color_h, (20,20), 13, 2)
            pygame.draw.rect(self.base_image, color_h, (15,15,10,10))
            ex = int(20 + math.cos(math.radians(self.angle+90)) * 15)
            ey = int(20 - math.sin(math.radians(self.angle+90)) * 15)
            pygame.draw.line(self.base_image, (255,255,100), (20,20), (ex,ey), 2)

        if self.shield > 0:
            ratio = self.shield / self.max_shield
            sc = (0, int(100+155*ratio), 255) if not self.abyss_mode else (0,220,180)
            pygame.draw.circle(self.base_image, sc, (20,20), 19, 2)

        self.image = pygame.transform.rotate(self.base_image, self.angle)
        self.rect  = self.image.get_rect(center=(400,300))

    def set_dimension(self, dimension):
        self.dimension = dimension
        self._redraw()

    def get_fire_direction(self, mouse_pos):
        if mouse_pos:
            diff = Vector2(mouse_pos) - Vector2(400,300)
            if diff.length() > 0:
                return diff.normalize()
        rad = math.radians(self.angle+90)
        return Vector2(-math.cos(rad), math.sin(rad))

    def kill_combo(self):
        self.combo += 1
        self.combo_timer = 180
        self.max_combo = max(self.max_combo, self.combo)
        self.kill_count += 1
        return self.combo

    def get_combo_multiplier(self):
        if self.combo < 5:  return 1.0
        if self.combo < 10: return 1.5
        if self.combo < 20: return 2.0
        if self.combo < 30: return 3.0
        return 5.0

    def take_hit(self, dmg):
        if self.shield > 0:
            absorbed = min(self.shield, dmg)
            self.shield -= absorbed
            dmg -= absorbed
        self.health -= dmg
        self.invincible = 60
        return dmg


# ─────────────────────────────────────────
#  ROBOT COMPANION
# ─────────────────────────────────────────
class RobotCompanion(pygame.sprite.Sprite):
    def __init__(self, owner):
        super().__init__()
        self.owner       = owner
        self.world_pos   = Vector2(owner.world_pos)
        self.orbit_angle = 0
        self.timer       = 0
        self.shoot_cd    = 25
        self.image       = pygame.Surface((22,22), pygame.SRCALPHA)
        self.rect        = self.image.get_rect()
        self._draw()

    def _draw(self):
        self.image.fill((0,0,0,0))
        pygame.draw.rect(self.image, (80,180,255), (3,5,16,12))
        pygame.draw.rect(self.image, (40,90,150),  (3,5,16,12), 1)
        pygame.draw.rect(self.image, (60,160,230), (7,1,8,6))
        pygame.draw.circle(self.image, (0,255,200), (9,4), 2)
        pygame.draw.circle(self.image, (0,255,200), (13,4), 2)

    def update(self, enemies, projectiles, dimension, camera_offset):
        self.orbit_angle = (self.orbit_angle + 2.5) % 360
        r = 55
        self.world_pos = self.owner.world_pos + Vector2(
            math.cos(math.radians(self.orbit_angle)) * r,
            math.sin(math.radians(self.orbit_angle)) * r,
        )
        sx = int(self.world_pos.x - camera_offset.x)
        sy = int(self.world_pos.y - camera_offset.y)
        self.rect.center = (sx, sy)
        self.timer += 1
        if self.timer >= self.shoot_cd:
            self.timer = 0
            nearest, min_d = None, 420
            for e in enemies:
                if e.dimension_type == dimension:
                    d = (e.world_pos - self.world_pos).length()
                    if d < min_d:
                        min_d = d; nearest = e
            if nearest:
                d = nearest.world_pos - self.world_pos
                projectiles.add(Projectile(
                    self.world_pos, d.normalize(), dimension,
                    color_override=(0,255,180), speed=11, dmg=1, is_direction=True))


# ─────────────────────────────────────────
#  ENEMY DATA
# ─────────────────────────────────────────
ENEMY_DATA = {
    "basic_drone":   {"name":"기본 드론",  "hp":1,"speed":1.9,"size":24,"cp":(0,150,255),"cv":(50,50,200),"shape":"circle","behavior":"chase","gem":1},
    "swarm_organism":{"name":"군집 유기체","hp":1,"speed":2.4,"size":20,"cp":(80,200,80),"cv":(40,140,40),"shape":"triangle","behavior":"swarm","gem":1},
    "glitcher":      {"name":"글리처",     "hp":1,"speed":3.0,"size":20,"cp":(200,0,200),"cv":(255,0,255),"shape":"rect","behavior":"zigzag","gem":1},
    "hunter_drone":  {"name":"헌터 드론",  "hp":2,"speed":2.8,"size":22,"cp":(220,110,50),"cv":(160,50,0),"shape":"triangle","behavior":"chase","gem":1},
    "sentinel":      {"name":"감시자",     "hp":3,"speed":1.3,"size":26,"cp":(100,100,200),"cv":(50,50,120),"shape":"rect","behavior":"orbit","gem":2},
    "sniper_node":   {"name":"저격 노드",  "hp":2,"speed":0.8,"size":20,"cp":(255,255,100),"cv":(200,200,0),"shape":"diamond","behavior":"snipe","gem":2,"special":"ranged_shot"},
    "elite_enforcer":{"name":"엘리트",     "hp":5,"speed":2.1,"size":26,"cp":(220,50,50),"cv":(160,0,0),"shape":"rect","behavior":"chase","gem":3,"special":"armor"},
    "void_weaver":   {"name":"공허 방직자","hp":5,"speed":1.7,"size":28,"cp":(80,80,80),"cv":(0,220,220),"shape":"diamond","behavior":"orbit","gem":3,"special":"slow_field"},
    "corrupted_sentry":{"name":"오염된 센트리","hp":6,"speed":1.5,"size":28,"cp":(140,140,0),"cv":(0,255,0),"shape":"circle","behavior":"chase","gem":3,"special":"poison_on_death"},
    "shadow_lurker": {"name":"그림자 잠복자","hp":3,"speed":3.8,"size":22,"cp":(50,50,50),"cv":(10,10,10),"shape":"triangle","behavior":"zigzag","gem":3,"special":"dash"},
    # 심해 전용
    "abyss_eel":     {"name":"심해 뱀장어","hp":4,"speed":2.5,"size":22,"cp":(0,100,150),"cv":(0,200,255),"shape":"triangle","behavior":"zigzag","gem":2,"special":"poison_on_death"},
    "depth_guardian":{"name":"심해 수호자","hp":8,"speed":1.0,"size":32,"cp":(0,60,120),"cv":(0,150,200),"shape":"rect","behavior":"orbit","gem":4,"special":"armor"},
    "leviathan_eye": {"name":"리바이어던의 눈","hp":15,"speed":0.7,"size":40,"cp":(0,40,100),"cv":(0,100,200),"shape":"circle","behavior":"snipe","gem":8,"special":"ranged_shot"},
    # 허공 차원 전용
    "null_fragment":  {"name":"공백 파편", "hp":1,"speed":4.5,"size":18,"cp":(180,180,200),"cv":(220,220,255),"shape":"diamond","behavior":"chase","gem":1},
    "void_titan":     {"name":"공허 타이탄","hp":20,"speed":1.2,"size":50,"cp":(60,0,120),"cv":(120,0,255),"shape":"circle","behavior":"orbit","gem":10,"special":"burst_shot"},
    "echo_phantom":   {"name":"에코 팬텀",  "hp":6,"speed":2.8,"size":26,"cp":(150,150,200),"cv":(200,100,255),"shape":"diamond","behavior":"zigzag","gem":3,"special":"dash"},
    # 중간 보스
    "anomaly_core":        {"name":"이상 현상 코어","hp":30,"speed":0.9,"size":48,"cp":(100,160,220),"cv":(220,60,255),"shape":"circle","behavior":"orbit","gem":12,"special":"summon","spawn_progress":0.25},
    "dreadnought_construct":{"name":"드레드노트","hp":50,"speed":1.1,"size":58,"cp":(90,90,90),"cv":(160,0,0),"shape":"rect","behavior":"chase","gem":15,"special":"burst_shot","spawn_progress":0.50},
    "echo_wraith":         {"name":"메아리 망령","hp":38,"speed":2.2,"size":44,"cp":(130,130,160),"cv":(50,255,50),"shape":"diamond","behavior":"zigzag","gem":15,"special":"clone","spawn_progress":0.70},
    "abyss_leviathan":     {"name":"심연의 리바이어던","hp":80,"speed":0.8,"size":70,"cp":(0,50,120),"cv":(0,150,255),"shape":"circle","behavior":"orbit","gem":25,"special":"burst_shot","spawn_progress":0.55},
    "null_colossus":       {"name":"공백 거신","hp":60,"speed":1.4,"size":64,"cp":(100,100,140),"cv":(180,50,255),"shape":"rect","behavior":"chase","gem":20,"special":"phase_boss","spawn_progress":0.60},
    # 최종 보스
    "nexus_overmind":  {"name":"넥서스 오버마인드","hp":150,"speed":0.9,"size":80,"cp":(180,180,210),"cv":(255,0,255),"shape":"circle","behavior":"orbit","gem":40,"special":"phase_boss","phase_count":3,"spawn_progress":0.85},
    "abyssal_tyrant":  {"name":"심연의 폭군","hp":200,"speed":1.3,"size":90,"cp":(80,0,0),"cv":(0,255,150),"shape":"circle","behavior":"chase","gem":50,"special":"phase_boss","phase_count":3,"spawn_progress":0.90},
    "void_god":        {"name":"공허의 신","hp":250,"speed":1.0,"size":100,"cp":(60,0,120),"cv":(255,200,255),"shape":"circle","behavior":"orbit","gem":60,"special":"phase_boss","phase_count":4,"spawn_progress":0.88},
    "abyss_sovereign": {"name":"심연의 군주","hp":300,"speed":0.7,"size":110,"cp":(0,30,80),"cv":(0,200,255),"shape":"circle","behavior":"chase","gem":70,"special":"phase_boss","phase_count":4,"spawn_progress":0.92},
    # 제3차원 블랙홀 보스 — 블랙홀에 흡입될 때만 등장 (다양한 종류)
    "rift_guardian":   {"name":"균열의 수호자","hp":120,"speed":1.5,"size":80,"cp":(120,0,180),"cv":(255,50,255),"shape":"circle","behavior":"orbit","gem":30,"special":"phase_boss","phase_count":3},
    "rift_devourer":   {"name":"균열의 포식자","hp":160,"speed":2.0,"size":86,"cp":(200,0,100),"cv":(255,100,0),"shape":"triangle","behavior":"chase","gem":35,"special":"phase_boss","phase_count":3},
    "rift_colossus":   {"name":"균열의 거신",  "hp":200,"speed":1.0,"size":100,"cp":(80,80,200),"cv":(200,200,255),"shape":"rect","behavior":"orbit","gem":40,"special":"phase_boss","phase_count":4},
    "void_wraith_king":{"name":"공허 망령왕",  "hp":140,"speed":2.8,"size":76,"cp":(50,0,100),"cv":(200,50,255),"shape":"diamond","behavior":"zigzag","gem":32,"special":"phase_boss","phase_count":3},
    "abyss_rift_lord": {"name":"심연 균열군주","hp":240,"speed":0.8,"size":110,"cp":(0,20,80),"cv":(0,150,255),"shape":"circle","behavior":"snipe","gem":50,"special":"phase_boss","phase_count":4},
    "entropy_core":    {"name":"엔트로피 코어","hp":180,"speed":1.6,"size":90,"cp":(200,100,0),"cv":(255,200,50),"shape":"circle","behavior":"orbit","gem":38,"special":"phase_boss","phase_count":3},
}


# ─────────────────────────────────────────
#  ENEMY CLASS
# ─────────────────────────────────────────
class Enemy(pygame.sprite.Sprite):
    def __init__(self, world_pos, dimension_type, etype="basic_drone", difficulty=1.0):
        super().__init__()
        self.dimension_type = dimension_type
        self.etype          = etype
        data                = ENEMY_DATA.get(etype, ENEMY_DATA["basic_drone"])
        sz = data["size"]
        self.image     = pygame.Surface((sz,sz), pygame.SRCALPHA)
        self.rect      = self.image.get_rect()
        self.world_pos = Vector2(world_pos)
        self.pos       = self.world_pos
        self.vel       = Vector2(0,0)
        self.speed     = data["speed"] * (1 + difficulty * 0.15)
        self.hp        = int(data["hp"] * (1 + difficulty * 0.1))
        self.max_hp    = self.hp
        self.gem_val   = data.get("gem",1)
        self.special   = data.get("special",None)
        self.behavior  = data["behavior"]
        self.name      = data["name"]
        self.special_timer = 0
        self.phase     = 1
        self.orbit_angle = random.uniform(0,360)
        self._draw()

    def _draw(self):
        data = ENEMY_DATA.get(self.etype, ENEMY_DATA["basic_drone"])
        sz   = data["size"]
        if self.image.get_size() != (sz,sz):
            self.image = pygame.Surface((sz,sz), pygame.SRCALPHA)
        self.image.fill((0,0,0,0))
        cp = data["cp"] if self.dimension_type=="PHYSICAL" else data["cv"]
        cx,cy,r = sz//2, sz//2, sz//2-2
        white = (255,255,255)
        shape = data["shape"]
        if shape == "circle":
            pygame.draw.circle(self.image, cp, (cx,cy), r)
            if data["hp"] >= 20: pygame.draw.circle(self.image, (255,200,0), (cx,cy), r, 3)
            elif data["hp"] >= 5: pygame.draw.circle(self.image, white, (cx,cy), r, 1)
        elif shape == "triangle":
            pygame.draw.polygon(self.image, cp, [(cx,2),(sz-2,sz-2),(2,sz-2)])
        elif shape == "rect":
            pygame.draw.rect(self.image, cp, (2,2,sz-4,sz-4))
            pygame.draw.rect(self.image, white, (2,2,sz-4,sz-4), 1)
            if data["hp"] >= 5: pygame.draw.rect(self.image, (255,200,0),(2,2,sz-4,sz-4), 2)
        elif shape == "diamond":
            pygame.draw.polygon(self.image, cp, [(cx,2),(sz-2,cy),(cx,sz-2),(2,cy)])
            pygame.draw.polygon(self.image, white, [(cx,2),(sz-2,cy),(cx,sz-2),(2,cy)], 1)
        if self.special == "phase_boss" and self.phase >= 2:
            pygame.draw.circle(self.image, (255,50,50), (cx,cy), r, 3)

    def update_screen_pos(self, camera_offset):
        sx = int(self.world_pos.x - camera_offset.x)
        sy = int(self.world_pos.y - camera_offset.y)
        self.rect.center = (sx,sy)

    def update(self, player_world_pos, enemy_projectiles=None, dimension=None, all_enemies=None):
        self.special_timer += 1
        self._do_behavior(player_world_pos, all_enemies)
        if enemy_projectiles is not None and dimension is not None:
            self._try_shoot(player_world_pos, enemy_projectiles, dimension)
        self.pos = self.world_pos

    def _try_shoot(self, player_pos, eprojs, dimension):
        if self.dimension_type != dimension: return
        d_vec = player_pos - self.world_pos
        dist  = d_vec.length()
        if self.special == "ranged_shot" and self.special_timer % 90 == 0 and dist < 500:
            eprojs.add(EnemyProjectile(self.world_pos, d_vec.normalize(), dimension, color=(255,255,0), speed=6, dmg=8))
        if self.special == "burst_shot" and self.special_timer % 80 == 0:
            for a in range(0,360,45):
                v = Vector2(math.cos(math.radians(a)), math.sin(math.radians(a)))
                eprojs.add(EnemyProjectile(self.world_pos, v, dimension, color=(255,80,0), speed=5, dmg=5))
        if self.special == "phase_boss" and self.special_timer % 60 == 0:
            for a in range(0,360,90):
                v = Vector2(math.cos(math.radians(a+self.special_timer)), math.sin(math.radians(a+self.special_timer)))
                eprojs.add(EnemyProjectile(self.world_pos, v, dimension, color=(255,0,100), speed=4+self.phase, dmg=8+self.phase*3))

    def _do_behavior(self, player_pos, all_enemies):
        to_player = player_pos - self.world_pos
        dist      = to_player.length()
        chase_dir = to_player.normalize() if dist > 0 else Vector2(0,1)
        if self.behavior == "chase":
            self.vel = chase_dir * self.speed
        elif self.behavior == "swarm":
            flock = self._boid(all_enemies)
            move  = chase_dir * self.speed + flock
            if move.length() > self.speed*1.6: move = move.normalize()*self.speed*1.6
            self.vel = move
        elif self.behavior == "zigzag":
            perp = Vector2(-chase_dir.y, chase_dir.x)
            wave = math.sin(self.special_timer * 0.12) * 1.5
            self.vel = (chase_dir + perp * wave).normalize() * self.speed
        elif self.behavior == "orbit":
            self.orbit_angle += 1.5
            target = player_pos + Vector2(math.cos(math.radians(self.orbit_angle))*200,
                                          math.sin(math.radians(self.orbit_angle))*200)
            d = target - self.world_pos
            self.vel = d.normalize() * self.speed if d.length() > 0 else Vector2(0,0)
        elif self.behavior == "snipe":
            if dist > 350:   self.vel = chase_dir * self.speed
            elif dist < 200: self.vel = -chase_dir * self.speed
            else:            self.vel *= 0.9
        if self.special == "dash" and self.special_timer % 120 == 0:
            self.vel = chase_dir * self.speed * 5
        self.world_pos += self.vel

    def _boid(self, all_enemies):
        if not all_enemies: return Vector2(0,0)
        sep=Vector2(0,0); coh=Vector2(0,0); ali=Vector2(0,0); n=0
        for o in all_enemies:
            if o is self: continue
            d = (o.world_pos - self.world_pos).length()
            if 0 < d < 50: sep -= (o.world_pos - self.world_pos).normalize()*(50-d)*0.06
            if d < 110:    coh += o.world_pos; ali += o.vel; n += 1
        if n: coh=(coh/n-self.world_pos)*0.012; ali=(ali/n)*0.05
        return sep+coh+ali

    def take_damage(self, dmg):
        if self.special == "armor": dmg = max(1, dmg-1)
        self.hp -= dmg
        if self.special == "phase_boss":
            ratio     = self.hp / self.max_hp
            new_phase = 3 if ratio < 0.33 else (2 if ratio < 0.66 else 1)
            if hasattr(self, 'max_hp') and self.max_hp >= 100:
                new_phase = 4 if ratio < 0.25 else (3 if ratio < 0.50 else (2 if ratio < 0.75 else 1))
            if new_phase != self.phase:
                self.phase = new_phase
                self.speed *= 1.25
                self._draw()
        return self.hp <= 0


# ─────────────────────────────────────────
#  PROJECTILE (player)
# ─────────────────────────────────────────
class Projectile(pygame.sprite.Sprite):
    def __init__(self, world_pos, direction, dimension,
                 color_override=None, speed=8, dmg=1, is_direction=True, size=5):
        super().__init__()
        self.dimension = dimension
        self.dmg       = dmg
        self.world_pos = Vector2(world_pos)
        sz = max(size,4)*2
        self.image = pygame.Surface((sz,sz), pygame.SRCALPHA)
        color = color_override or ((0,255,255) if dimension=="PHYSICAL" else (255,0,255))
        r = sz//2
        pygame.draw.circle(self.image, color, (r,r), r-1)
        pygame.draw.circle(self.image, (255,255,255), (r,r), max(1,r-3))
        self.rect = self.image.get_rect()
        self.vel  = Vector2(direction).normalize()*speed if Vector2(direction).length()>0 else Vector2(0,-speed)
        self.life = 0

    def update_screen_pos(self, camera_offset):
        self.rect.center = (int(self.world_pos.x-camera_offset.x),
                            int(self.world_pos.y-camera_offset.y))

    def update(self):
        self.world_pos += self.vel
        self.life += 1
        if self.life > 130: self.kill()


# ─────────────────────────────────────────
#  ENEMY PROJECTILE
# ─────────────────────────────────────────
class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, world_pos, direction, dimension, color=(255,80,80), speed=5, dmg=5):
        super().__init__()
        self.dimension = dimension
        self.dmg       = dmg
        self.world_pos = Vector2(world_pos)
        sz = 14
        self.image = pygame.Surface((sz,sz), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (sz//2,sz//2), sz//2-1)
        pygame.draw.circle(self.image, (255,255,255), (sz//2,sz//2), max(1,sz//2-4))
        self.rect = self.image.get_rect()
        self.vel  = Vector2(direction).normalize()*speed if Vector2(direction).length()>0 else Vector2(0,speed)
        self.life = 0

    def update_screen_pos(self, camera_offset):
        self.rect.center = (int(self.world_pos.x-camera_offset.x),
                            int(self.world_pos.y-camera_offset.y))

    def update(self):
        self.world_pos += self.vel
        self.life += 1
        if self.life > 220: self.kill()


# ─────────────────────────────────────────
#  GEM
# ─────────────────────────────────────────
class Gem(pygame.sprite.Sprite):
    def __init__(self, world_pos, value=1):
        super().__init__()
        self.value     = value
        self.world_pos = Vector2(world_pos)
        self.pos       = self.world_pos
        self.age       = 0
        self.image     = pygame.Surface((14,14), pygame.SRCALPHA)
        c = {1:(0,255,100),3:(0,150,255),5:(255,200,0),8:(255,100,0),10:(255,50,200)}.get(value,(0,255,100))
        pygame.draw.polygon(self.image, c, [(7,0),(14,7),(7,14),(0,7)])
        pygame.draw.polygon(self.image, (255,255,255), [(7,0),(14,7),(7,14),(0,7)], 1)
        self.rect = self.image.get_rect()

    def update_screen_pos(self, camera_offset):
        self.rect.center = (int(self.world_pos.x-camera_offset.x),
                            int(self.world_pos.y-camera_offset.y))

    def update(self):
        self.age += 1


# ─────────────────────────────────────────
#  STRUCTURE
# ─────────────────────────────────────────
class Structure(pygame.sprite.Sprite):
    def __init__(self, rect_tuple, color=(50,50,60), border=(80,80,100)):
        super().__init__()
        self.wx, self.wy = rect_tuple[0], rect_tuple[1]
        self.w,  self.h  = rect_tuple[2], rect_tuple[3]
        self.image = pygame.Surface((self.w,self.h))
        self.image.fill(color)
        pygame.draw.rect(self.image, border, (0,0,self.w,self.h), 2)
        self.rect = self.image.get_rect()

    def update_screen_pos(self, camera_offset):
        self.rect.topleft = (int(self.wx-camera_offset.x), int(self.wy-camera_offset.y))

    def get_world_rect(self):
        return pygame.Rect(self.wx, self.wy, self.w, self.h)


# ─────────────────────────────────────────
#  FLUID
# ─────────────────────────────────────────
class Fluid(pygame.sprite.Sprite):
    def __init__(self, rect_tuple, color=(0,50,200,80)):
        super().__init__()
        self.wx, self.wy = rect_tuple[0], rect_tuple[1]
        self.w,  self.h  = rect_tuple[2], rect_tuple[3]
        self.image = pygame.Surface((self.w,self.h), pygame.SRCALPHA)
        self.image.fill(color)
        self.rect  = self.image.get_rect()
        self.friction_mult = 0.5
        self.buoyancy      = -0.3

    def update_screen_pos(self, camera_offset):
        self.rect.topleft = (int(self.wx-camera_offset.x), int(self.wy-camera_offset.y))

    def get_world_rect(self):
        return pygame.Rect(self.wx, self.wy, self.w, self.h)