import pygame
from pygame.math import Vector2
import random
import math
import os

_bh_font = [None]  # Blackhole 타이머 폰트 캐시 (pygame.init 후 첫 사용 시 초기화)

# ─────────────────────────────────────────
#  GLOBAL SETTINGS  (런타임 감도/물리 설정)
# ─────────────────────────────────────────
class GameSettings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_defaults()
        return cls._instance

    def _init_defaults(self):
        # SHIP 모드  ──  속도 대폭 상향 
        self.ship_accel        = 0.80   # ↑ 0.38→0.80
        self.ship_max_speed    = 11.0   # ↑ 5.5→11.0
        self.ship_friction     = 0.90   # ↑ 0.82→0.90 (미끄러짐 증가)
        self.ship_rotate_speed = 0.28   # ↑ 0.18→0.28

        # HUMAN 모드
        self.human_accel       = 1.6    # ↑ 0.9→1.6
        self.human_base_speed  = 3.0    # ↑ 1.5→3.0

        # DASH  ──  대쉬 강화 
        self.dash_speed        = 32     # ↑ 20→32
        self.dash_frames       = 12     # ↑ 10→12
        self.dash_cooldown     = 35     # ↓ 50→35 (더 자주)

        # 카메라
        self.camera_smooth     = 0.14   # 살짝 빠르게

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

SETTINGS = GameSettings()

# ─────────────────────────────────────────
#  WEAPONS
# ─────────────────────────────────────────
WEAPONS = {
    "laser":       {"name":"P-11 플라즈마", "cooldown":18,"speed":14,"dmg":1, "color_p":(0,255,255),  "color_v":(255,0,255),  "size":5, "spread":0,  "count":1},
    "shotgun":     {"name":"보이드 블릿저",   "cooldown":38,"speed":10,"dmg":2, "color_p":(255,200,0),  "color_v":(255,100,0),  "size":4, "spread":22, "count":6},
    "sniper":      {"name":"컨티뉴엄 레일",    "cooldown":55,"speed":22,"dmg":4, "color_p":(200,255,200),"color_v":(100,255,200),"size":3, "spread":0,  "count":1},
    "gatling":     {"name":"파티클 슈레더",   "cooldown":5, "speed":11,"dmg":1, "color_p":(255,150,50), "color_v":(200,50,255), "size":4, "spread":10, "count":1},
    "rocket":      {"name":"중력 붕괴탄",    "cooldown":75,"speed":8, "dmg":6, "color_p":(255,80,80),  "color_v":(180,0,180),  "size":8, "spread":0,  "count":1},
    "robot_arm":   {"name":"드론 센티넬",  "cooldown":14,"speed":12,"dmg":2, "color_p":(100,200,255),"color_v":(200,100,255),"size":6, "spread":5,  "count":2},
    "plasma":      {"name":"태양점 방사기",    "cooldown":28,"speed":9, "dmg":3, "color_p":(180,0,255),  "color_v":(0,255,180),  "size":9, "spread":5,  "count":3},
    "railgun":     {"name":"오메가 레일건",     "cooldown":90,"speed":28,"dmg":8, "color_p":(255,255,0),  "color_v":(255,100,0),  "size":4, "spread":0,  "count":1},
    "void_cannon": {"name":"심해 싱귤래리티",  "cooldown":45,"speed":7, "dmg":5, "color_p":(80,0,180),   "color_v":(0,220,255),  "size":12,"spread":0,  "count":1},
    "abyss_beam":  {"name":"고압 버스트",  "cooldown":8, "speed":16,"dmg":2, "color_p":(0,80,200),   "color_v":(200,0,100),  "size":5, "spread":2,  "count":2},
    "shockwave":   {"name":"노바 임팩트", "cooldown":60,"speed":3, "dmg":8, "color_p":(255,180,0),  "color_v":(0,255,255),  "size":18,"spread":0,  "count":1},
    "spiral_laser":{"name":"네뷸라 스파이럴", "cooldown":10,"speed":13,"dmg":2, "color_p":(255,80,200), "color_v":(80,255,80),  "size":6, "spread":45, "count":4},
    "thunder_spear": {"name":"천둥의 창", "cooldown":15,"speed":18,"dmg":5, "color_p":(255,255,100), "color_v":(255,255,255), "size":8, "spread":0, "count":1},
    "void_blade":    {"name":"공허의 검", "cooldown":10,"speed":12,"dmg":6, "color_p":(150,0,255), "color_v":(0,0,0), "size":10, "spread":0, "count":1},
    "omega_ray":     {"name":"오메가 레이", "cooldown":20,"speed":25,"dmg":10, "color_p":(255,255,255), "color_v":(255,0,0), "size":4, "spread":0, "count":1},
}
WEAPON_ORDER        = ["laser","shotgun","sniper","gatling","rocket","robot_arm","plasma","railgun","void_cannon","abyss_beam","shockwave","spiral_laser"]
WEAPON_UNLOCK_LEVEL = [1,      3,        5,       8,        12,      16,         20,      25,       30,           35,          40,          45]

# ─────────────────────────────────────────
#  PERSISTENT UPGRADES & SKILLS
# ─────────────────────────────────────────
PERSISTENT_UPGRADES = {
    "shield_boost": {"name": "강화 쉴드", "cost": 50, "currency": "gold", "desc": "최대 쉴드 +5", "max_lvl": 10},
    "speed_boost":  {"name": "엔진 오버클럭", "cost": 100, "currency": "gold", "desc": "이동 속도 +3%", "max_lvl": 10},
    "hp_boost":     {"name": "선체 보강", "cost": 80, "currency": "gold", "desc": "최대 HP +10", "max_lvl": 10},
    "xp_bonus":     {"name": "신경 링크",      "cost": 5, "currency": "diamond", "desc": "경험치 획득 +5%", "max_lvl": 5},
    "dash_cdr":     {"name": "플럭스 커패시터",   "cost": 12, "currency": "diamond", "desc": "대쉬 쿨타임 -5%", "max_lvl": 10},
    "dmg_boost":    {"name": "오메가 코어",       "cost": 15, "currency": "diamond", "desc": "공격력 +10%", "max_lvl": 5},
}

active_skills = {
    "nova_blast":      {"name": "노바 블래스트",   "desc": "주변 모든 적에게 강력한 광역 데미지", "cd": 600, "max_lvl": 10, "color": (255, 120, 0)},
    "time_warp":       {"name": "타임 워프",    "desc": "시간을 왜곡하여 모든 적의 속도 감소", "cd": 1200, "max_lvl": 5, "color": (100, 255, 255)},
    "vampirism":       {"name": "뱀파이어리즘",    "desc": "적 사살 시 일정량 체력 회복 (지속 효과)", "cd": 1800, "max_lvl": 5, "color": (255, 50, 50)},
    "shield_overload": {"name": "쉴드 오버로드",   "desc": "쉴드 즉시 완충 및 5초간 공격력 +50%", "cd": 900, "max_lvl": 10, "color": (255, 255, 255)},
    "gravity_surge":   {"name": "중력 서지",      "desc": "마우스 위치에 5초간 블랙홀 생성", "cd": 1500, "max_lvl": 8, "color": (150, 0, 255)},
    "stealth_cloak":   {"name": "스텔스 클로킹",   "desc": "5초간 무적 및 이동 속도 대폭 증가", "cd": 2000, "max_lvl": 5, "color": (180, 180, 200)},
    "shadow_extraction":{"name": "그림자 추출",    "desc": "나혼렙: 그림자 병사를 소환하여 함께 전투", "cd": 2400, "max_lvl": 5, "color": (100, 0, 255)},
    "getsuga_tensho":  {"name": "월아천충",      "desc": "블리치: 거대한 보이드 에너지를 방출", "cd": 800, "max_lvl": 10, "color": (255, 0, 0)},
    "infinite_void":   {"name": "무량공처",      "desc": "주술회전: 모든 적을 빙결시키고 에너지를 속박", "cd": 3600, "max_lvl": 3, "color": (255, 255, 255)},
    "titan_form":      {"name": "진격의 거인",   "desc": "진격거: 거대화하여 무적 상태로 적을 짓밟음", "cd": 3000, "max_lvl": 5, "color": (200, 100, 50)},
    "thunder_spear":   {"name": "뇌창",         "desc": "진격거: 강력한 폭발을 일으키는 투척 병기", "cd": 1000, "max_lvl": 10, "color": (255, 230, 0)},
    "amaterasu":       {"name": "아마테라스",    "desc": "나루토: 영구적인 흑염으로 적을 불태움", "cd": 1800, "max_lvl": 5, "color": (50, 0, 80)},
    "hollow_purple":    {"name": "허식 자",      "desc": "주술회전: 창과 적을 융합하여 전방 소멸", "cd": 2400, "max_lvl": 5, "type": "charge", "color": (200, 0, 255)},
    "gomu_gatling":    {"name": "고무고무 가틀링", "desc": "원피스: 5초간 전방향 무차별 난타", "cd": 1800, "max_lvl": 10, "color": (255, 200, 150)},
    "izanagi":         {"name": "이자나기",      "desc": "나루토: 사망 시 1회 고정 부활 (패시브)", "cd": 7200, "max_lvl": 3, "type": "passive", "color": (0, 255, 120)},
}
ACTIVE_SKILLS = active_skills

RUNESTONES = {
    "naruto": {
        "name": "나루토 룬석",
        "desc": "닌자의 차크라를 다루는 룬석",
        "color": (255, 140, 0),
        "max_lvl": 10,
        "base_cost": 3000,
        "currency": "gold",
        "unlocks": {
            1: "amaterasu",
            5: "izanagi",
        }
    },
    "jujutsu": {
        "name": "주술회전 룬석",
        "desc": "주력을 통제하는 룬석",
        "color": (180, 0, 255),
        "max_lvl": 10,
        "base_cost": 4000,
        "currency": "gold",
        "unlocks": {
            1: "hollow_purple",
            5: "infinite_void",
        }
    },
    "aot": {
        "name": "진격거 룬석",
        "desc": "거인의 힘을 다루는 룬석",
        "color": (255, 100, 50),
        "max_lvl": 10,
        "base_cost": 3500,
        "currency": "gold",
        "unlocks": {
            1: "thunder_spear",
            5: "titan_form",
        }
    },
    "sololeveling": {
        "name": "나혼렙 룬석",
        "desc": "그림자 군주의 룬석",
        "color": (100, 0, 255),
        "max_lvl": 10,
        "base_cost": 100,
        "currency": "diamond",
        "unlocks": {
            1: "shadow_extraction",
        }
    },
    "bleach": {
        "name": "블리치 룬석",
        "desc": "사신의 영압을 다루는 룬석",
        "color": (255, 0, 0),
        "max_lvl": 10,
        "base_cost": 2500,
        "currency": "gold",
        "unlocks": {
            1: "getsuga_tensho",
        }
    },
    "onepiece": {
        "name": "원피스 룬석",
        "desc": "패기와 열매의 룬석",
        "color": (255, 200, 0),
        "max_lvl": 10,
        "base_cost": 5000,
        "currency": "gold",
        "unlocks": {
            1: "gomu_gatling",
        }
    },
    "cosmic": {
        "name": "우주 룬석",
        "desc": "기본 차원 제어 룬석",
        "color": (0, 255, 255),
        "max_lvl": 15,
        "base_cost": 1500,
        "currency": "gold",
        "unlocks": {
            1: "nova_blast",
            3: "vampirism",
            5: "stealth_cloak",
            7: "shield_overload",
            9: "time_warp",
            11: "gravity_surge",
        }
    }
}
RUNESTONE_ORDER = ["cosmic", "naruto", "jujutsu", "sololeveling", "bleach", "aot", "onepiece"]



# ─────────────────────────────────────────
#  SHIP FORMS
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
        "speed_mult": 1.1, "dmg_mult": 1.1, "cd_mult": 1.0,
        "poly": [(18,0),(36,36),(18,26),(0,36)],
        "engine_pos": [(18,30)], "engine_r": 4,
    },
    "cruiser": {
        "name": "순양함 (Cruiser)",
        "color_p": (80,200,255), "color_v": (200,80,255),
        "desc": "방어 성능 특화 · 탄 2발 추가 · 이동속도 -20%",
        "speed_mult": 0.8, "dmg_mult": 1.0, "cd_mult": 0.85,
        "poly": [(18,0),(36,20),(30,36),(18,28),(6,36),(0,20)],
        "engine_pos": [(8,32),(28,32)], "engine_r": 3,
        "hp_bonus": 50,
    },
    "stealth": {
        "name": "스텔스 (Stealth)",
        "color_p": (120,120,180), "color_v": (180,60,255),
        "desc": "극강의 기동성 · 대쉬 쿨타임 -40% · 낮음 데미지 -20%",
        "speed_mult": 1.45, "dmg_mult": 0.8, "cd_mult": 1.1,
        "poly": [(18,0),(28,36),(18,22),(8,36)],
        "engine_pos": [(18,34)], "engine_r": 3,
        "dash_mult": 0.6,
    },
    "dreadnought": {
        "name": "드레드노트 (Dreadnought)",
        "color_p": (255,80,80), "color_v": (255,160,0),
        "desc": "화력 집중 · 데미지 ×2.2 · 극도로 느림(-45%)",
        "speed_mult": 0.55, "dmg_mult": 2.2, "cd_mult": 0.75,
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

_ship_images = {}
def get_ship_image(form_name, size=(40, 40)):
    key = (form_name, size)
    if key not in _ship_images:
        filename_map = {
            "fighter": "전투기",
            "cruiser": "순양함",
            "stealth": "스텔스",
            "dreadnought": "드레드노트",
            "abyss_ship": "심해함",
            "phantom": "팬텀"
        }
        fname_base = filename_map.get(form_name)
        frames = []
        if fname_base:
            for i in range(4):
                path = f"assets_frames/{fname_base}_{i}.png"
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        # Make it slightly larger so it fits well in the bounding box
                        # since the extracted canvas has a lot of padding for the flames.
                        # Wait, size is exactly the size we requested.
                        frames.append(pygame.transform.smoothscale(img, size))
                    except Exception as e:
                        pass
        if frames:
            _ship_images[key] = frames
        else:
            _ship_images[key] = None
    return _ship_images[key]

# ─────────────────────────────────────────
#  PARTICLE
# ─────────────────────────────────────────
class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, vel, color, life, size=3):
        super().__init__()
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
        ratio = self.life / self.max_life
        r = max(1, int(self.size * ratio))
        sx = int(self.pos.x - camera_offset.x)
        sy = int(self.pos.y - camera_offset.y)
        if -20 <= sx <= 820 and -20 <= sy <= 620:
            col = tuple(min(255, max(0, int(c * ratio))) for c in self.color)
            pygame.draw.circle(surface, col, (sx, sy), r)


# ─────────────────────────────────────────
#  BLACKHOLE
# ─────────────────────────────────────────
class Blackhole(pygame.sprite.Sprite):
    def __init__(self, world_pos):
        super().__init__()
        self.world_pos  = Vector2(world_pos)
        self.image = pygame.Surface((1,1), pygame.SRCALPHA) # Placeholder
        self.rect = self.image.get_rect()
        self.radius     = 0
        self.max_radius = 90
        self.age        = 0
        self.max_age    = 3600
        self.alive      = True
        self.spin_angle = 0
        self.pull_range = 350
        self.pull_force = 0.18

    def update(self):
        self.age += 1
        self.spin_angle = (self.spin_angle + 3) % 360
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
        # 회전 점: SRCALPHA 없이 색상 dim으로 근사
        dim_factor = (1 - self.age % 30 / 30) * (60 / 255)
        dot_col = (int(180 * dim_factor), 0, int(255 * dim_factor))
        for i in range(8):
            a = self.spin_angle + i * 45
            lx = cx + int(math.cos(math.radians(a)) * self.pull_range * 0.7)
            ly = cy + int(math.sin(math.radians(a)) * self.pull_range * 0.7)
            pygame.draw.circle(surface, dot_col, (lx, ly), 3)
        # 링: alpha를 색상 밝기로 근사
        for rad, alpha_val, col in [
            (self.radius + 30, 60,  (100, 0, 200)),
            (self.radius + 15, 100, (160, 0, 255)),
            (self.radius,      180, (200, 50, 255)),
        ]:
            if rad > 0:
                d = alpha_val / 255
                pygame.draw.circle(surface,
                    (int(col[0]*d), int(col[1]*d), int(col[2]*d)),
                    (cx, cy), rad, 3)
        # 코어: 단색으로 직접 그리기
        r = max(1, self.radius)
        pygame.draw.circle(surface, (0, 0, 0), (cx, cy), r)
        pygame.draw.circle(surface, (255, 100, 255), (cx, cy), max(1, r // 5))
        # 나선 팔: 2칸 간격으로 그려 연산 절반 감소
        for arm in range(3):
            base_angle = self.spin_angle * 2 + arm * 120
            for step in range(0, 20, 2):
                t   = step / 20
                rad = (self.radius + 10) * (0.2 + t * 0.8)
                ang = base_angle + t * 180
                px  = cx + int(math.cos(math.radians(ang)) * rad)
                py  = cy + int(math.sin(math.radians(ang)) * rad)
                d   = 1 - t
                col = (int(200 * d), int((50 + 80 * t) * d), int(255 * d))
                if col[0] > 5 or col[2] > 5:
                    pygame.draw.circle(surface, col, (px, py), 2)
        # 남은 시간 텍스트 (모듈 레벨 캐시 사용)
        if self.age < self.max_age - 60:
            remain = (self.max_age - self.age) // 60
            if _bh_font[0] is None:
                _bh_font[0] = pygame.font.SysFont(None, 16)
            txt = _bh_font[0].render(f"{remain}s", True, (200, 100, 255))
            surface.blit(txt, (cx - 10, cy - self.radius - 18))


# ─────────────────────────────────────────
#  PICKUP ITEM
# ─────────────────────────────────────────
ITEM_DATA = {
    "hp":          {"color": (0,255,80),    "label": "체력회복"},
    "shield":      {"color": (0,180,255),   "label": "쉴드보완"},
    "speed":       {"color": (255,100,255), "label": "속도향상"},
    "ammo":        {"color": (255,140,0),   "label": "탄약보급"},
    "ship_form":   {"color": (255,220,50),  "label": "기급변형"},
    "abyss_crystal":{"color":(0,220,255),   "label": "심해결정"},
    "crystal":     {"color": (255,255,255), "label": "크리스탈"},
    "overload":    {"color": (255,60,0),    "label": "과부하"},
}


# ─────────────────────────────────────────
class Portal(pygame.sprite.Sprite):
    def __init__(self, world_pos, target_universe="PRIME"):
        super().__init__()
        self.world_pos = Vector2(world_pos)
        self.target_universe = target_universe
        self.radius = 0
        self.max_radius = 110
        self.spin = 0
        self.active = True
        self.image = pygame.Surface((250, 250), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    def update(self):
        self.spin = (self.spin + 4) % 360
        if self.radius < self.max_radius:
            self.radius += 1.5
        self.rect.center = (int(self.world_pos.x), int(self.world_pos.y))

    def draw(self, surface, camera_offset, frame):
        cx = int(self.world_pos.x - camera_offset.x)
        cy = int(self.world_pos.y - camera_offset.y)
        if not (-150 <= cx <= 950 and -150 <= cy <= 750): return
        
        colors = {
            "PRIME": (0, 255, 255), "CYBER": (255, 255, 0),
            "ABYSSAL": (180, 0, 255), "GOLDEN": (255, 200, 50),
            "GLITCH": (255, 50, 50)
        }
        base_col = colors.get(self.target_universe, (255, 255, 255))
        
        for i in range(6):
            r = self.radius - i * 12
            if r > 0:
                alpha = int(180 * (r / self.max_radius))
                pygame.draw.circle(surface, (*base_col, alpha), (cx, cy), r, 2)
                angle_off = math.radians(self.spin * (1 + i*0.2) + i*60)
                for a in range(0, 360, 120):
                    rad = math.radians(a) + angle_off
                    px = cx + math.cos(rad) * r
                    py = cy + math.sin(rad) * r
                    pygame.draw.circle(surface, (255,255,255, alpha), (int(px), int(py)), 3)
        inner_r = int(self.radius * 0.3)
        if inner_r > 0:
            pulse = int(abs(math.sin(frame * 0.1)) * 100)
            pygame.draw.circle(surface, (255, 255, 255, 155 + pulse / 2), (cx, cy), inner_r)

# ─────────────────────────────────────────
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
        elif itype == "abyss_crystal":
            # 육각형 결정
            pts = [(9+int(8*math.cos(math.radians(60*i-30))),
                    9+int(8*math.sin(math.radians(60*i-30)))) for i in range(6)]
            pygame.draw.polygon(self.image, c, pts)
            pygame.draw.polygon(self.image, (255,255,255), pts, 1)
        elif itype == "overload":
            pygame.draw.polygon(self.image, c, [(9,0),(18,18),(0,18)])
            pygame.draw.circle(self.image, (255,200,0), (9,9), 4)
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
        self.DASH_SPEED  = 32
        self.DASH_FRAMES = 12
        self.DASH_CD     = 35

        self.speed_boost   = 0
        self.weapon_key    = "laser"
        self.unlocked_weapons = ["laser"]
        self._cd_bonus     = 0

        self.ship_form      = "fighter"
        self.form_morph_t   = 0
        self.form_prev      = "fighter"
        self.unlocked_forms = ["fighter"]

        self.ship_color_key = "cyan"

        self.abyss_mode     = False

        #  심해 잠수 시스템
        self.dive_active    = False   # 잠수 중
        self.dive_depth     = 0       # 현재 잠수 깊이 (0~100)
        self.dive_max       = 100
        self.dive_oxygen    = 300     # 산소 (프레임)
        self.dive_max_oxygen= 300
        self.dive_damage_cd = 0       # 산소 0일 때 데미지 쿨

        #  과부하 시스템
        self.overload_timer = 0       # >0 이면 과부하 활성

        #  연속 킬 streak (새 콤보 이펙트용)
        self.streak_kills   = 0
        self.streak_timer   = 0

        #  화폐 시스템 (금화, 다이아몬드)
        self.gold           = 0
        self.diamonds       = 0
        self.crystals       = 0
        self.upgrades       = {k: 0 for k in PERSISTENT_UPGRADES}

        #  스킬 시스템
        self.active_skills   = []   # 현재 보유 스킬
        self.skill_cooldowns = {k: 0 for k in ACTIVE_SKILLS}
        self.skill_use_count = {k: 0 for k in ACTIVE_SKILLS} #  스킬 숙련도 추적
        self.skill_vamp_timer = 0
        self.skill_dmg_timer = 0
        self.skill_stealth_timer = 0
        self.skill_titan_timer = 0
        self.skill_gatling_timer = 0 #  고무고무 가틀링 타이머
        self.skill_izanagi_ready = True #  이자나기 사용 가능 여부
        self.multiverse_type = "PRIME"

        self._speed_upg_mult = 1.0
        self._xp_upg_mult    = 1.0
        self._dash_cdr_mult  = 1.0
        self._dmg_upg_mult   = 1.0

        # 전직 시스템 — 플레이 통계 추적
        self.job_stats = {
            "melee_kills":    0,
            "range_kills":    0,
            "dash_count":     0,
            "skill_uses":     0,
            "damage_taken":   0,
            "weapon_switches":0,
            "dim_switches":   0,
            "max_combo":      0,
            "vamp_kills":     0,
        }
        self.job = None
        self._job_speed_mult    = 1.0
        self._job_dmg_mult      = 1.0
        self._job_skill_cd_mult = 1.0
        self._job_skill_dmg_mult= 1.0
        self._job_combo_bonus   = 0.0
        self._job_lifesteal_bonus = 0
        self._job_double_dash   = False
        self._job_void_immune   = False
        self._job_void_dmg_mult = 1.0
        # 직업 등급
        self.job_tier  = 0   # 0=초급 ~ 4=신화
        self.job_kills = 0   # 현재 직업 보유 중 처치 수
        self._job_tier_mult = 1.0
        
        # 스킬별 타이머
        self.skill_dmg_timer     = 0
        self.skill_stealth_timer = 0
        self.skill_vamp_timer    = 0
        self.skill_titan_timer   = 0



    @property
    def weapon(self):
        return WEAPONS[self.weapon_key]

    @property
    def weapon_cooldown(self):
        form  = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        cd_m  = form.get("cd_mult", 1.0)
        base  = max(3, int(self.weapon["cooldown"] * cd_m) - self._cd_bonus * 2)
        if self.overload_timer > 0:
            base = max(2, base // 2)   # 과부하: 사격속도 2배
        return base

    def get_dmg_mult(self):
        form = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        m = form.get("dmg_mult", 1.0)
        if hasattr(self, "_dmg_upg_mult"):
            m *= self._dmg_upg_mult
        if self.skill_dmg_timer > 0:
            m *= 1.5   # 스킬 데미지 버프
        if self.abyss_mode: m *= 1.3
        if self.overload_timer > 0: m *= 2.5   # 과부하: 데미지 2.5배
        if self.dive_active:
            # 잠수 깊이에 따라 데미지 보너스 (최대 +50%)
            m *= (1.0 + self.dive_depth / 200.0)
        if self.dimension == "VOID":
            m *= form.get("void_bonus", 1.0)
            
        #  멀티버스 데미지 보너스
        if self.multiverse_type == "ABYSSAL": m *= 1.5
        elif self.multiverse_type == "CYBER": m *= 1.1
        # 직업 데미지 배율 + 등급 보너스
        m *= getattr(self, "_job_dmg_mult", 1.0)
        m *= getattr(self, "_job_tier_mult", 1.0)
        # 차원술사: 공허 추가 데미지
        if self.dimension == "VOID":
            m *= getattr(self, "_job_void_dmg_mult", 1.0)
        return m

    def get_speed_mult(self):
        form = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        base = form.get("speed_mult", 1.0)
        if hasattr(self, "_speed_upg_mult"):
            base *= self._speed_upg_mult
        if self.dive_active:
            base *= max(0.4, 1.0 - self.dive_depth * 0.004)

        #  멀티버스 속도 보너스
        if self.multiverse_type == "CYBER": base *= 1.2
        elif self.multiverse_type == "GLITCH": base *= 1.15
        # 직업 속도 배율
        base *= getattr(self, "_job_speed_mult", 1.0)
        # 학살자: 콤보 5배마다 +5% 속도 (최대 +30%)
        if getattr(self, "_job_combo_bonus", 0) > 0:
            bonus = min(0.30, (self.combo // 5) * 0.05)
            base *= (1.0 + bonus)
        return base

    def get_dash_cd_mult(self):
        form = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        m = form.get("dash_mult", 1.0)
        if hasattr(self, "_dash_cdr_mult"):
            m *= self._dash_cdr_mult
        m *= getattr(self, "_job_skill_cd_mult", 1.0)  # 파일럿/광속 대쉬 쿨 감소
        return m

    def get_combo_multiplier(self):
        bonus = getattr(self, "_job_combo_bonus", 0.0)
        if self.combo < 5:  return 1.0 + bonus * 0.0
        if self.combo < 10: return 1.5 + bonus
        if self.combo < 20: return 2.0 + bonus * 1.5
        if self.combo < 30: return 3.0 + bonus * 2.0
        return 5.0 + bonus * 3.0

    def apply_job(self, job_key, job_data):
        """전직: 직업에 따른 스탯 적용 (재전직 시 이전 직업 효과 원복 후 적용)"""
        # 이전 직업 스탯 원복
        if self.job and hasattr(self, '_job_base_max_health'):
            self.max_health = self._job_base_max_health
            self.max_shield = self._job_base_max_shield
            self.health = min(self.health, self.max_health)
            self.shield = min(self.shield, self.max_shield)

        # 현재 스탯을 기준으로 저장
        self._job_base_max_health = self.max_health
        self._job_base_max_shield = self.max_shield

        self.job = job_key
        # HP 배율
        hp_mult = job_data.get("hp_mult", 1.0)
        self.max_health = int(self.max_health * hp_mult)
        self.health = min(self.health, self.max_health)
        # 쉴드 배율
        sh_mult = job_data.get("shield_mult", 1.0)
        self.max_shield = int(self.max_shield * sh_mult)
        self.shield = min(self.shield, self.max_shield)
        # 직업 등급 초기화
        self.job_tier  = 0
        self.job_kills = 0
        self._job_tier_mult = 1.0
        # 직업 전용 배율 저장
        self._job_speed_mult    = job_data.get("speed_mult", 1.0)
        self._job_dmg_mult      = job_data.get("dmg_mult", 1.0)
        self._job_skill_cd_mult = job_data.get("skill_cd_mult", 1.0)
        self._job_skill_dmg_mult= job_data.get("skill_dmg_mult", 1.0)
        self._job_combo_bonus   = job_data.get("combo_mult_bonus", 0.0)
        self._job_lifesteal_bonus = job_data.get("lifesteal_bonus", 0)
        self._job_double_dash   = job_data.get("double_dash", False)
        self._job_void_immune   = job_data.get("void_immune", False)
        self._job_void_dmg_mult = job_data.get("void_dmg_mult", 1.0)


    def check_job_tier_up(self):
        """직업 등급 상승 체크. 상승했으면 새 등급 인덱스 반환, 아니면 None."""
        if not self.job:
            return None
        kills_req = JOB_TIER_DATA["kills"]
        dmg_mults = JOB_TIER_DATA["dmg_mult"]
        max_tier = len(kills_req) - 1
        if self.job_tier >= max_tier:
            return None
        next_tier = self.job_tier + 1
        if self.job_kills >= kills_req[next_tier]:
            self.job_tier = next_tier
            self._job_tier_mult = dmg_mults[next_tier]
            return next_tier
        return None

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
        if form_key not in SHIP_FORMS: return
        if form_key == self.ship_form: return
        self.form_prev    = self.ship_form
        self.ship_form    = form_key
        self.form_morph_t = 0

    def try_dash(self, keys):
        cd = int(SETTINGS.dash_cooldown * self.get_dash_cd_mult())
        if self.dash_cd > 0: return False
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

    #  심해 잠수 업데이트
    def update_dive(self, diving_key_held, is_abyss_chapter):
        """심해 챕터에서만 동작하는 잠수 시스템"""
        if not is_abyss_chapter:
            self.dive_active = False
            self.dive_depth  = 0
            self.dive_oxygen = self.dive_max_oxygen
            return

        if diving_key_held:
            self.dive_active = True
            self.dive_depth  = min(self.dive_max, self.dive_depth + 0.8)
            self.dive_oxygen = max(0, self.dive_oxygen - 1)
        else:
            self.dive_active = False
            self.dive_depth  = max(0, self.dive_depth - 1.5)
            self.dive_oxygen = min(self.dive_max_oxygen, self.dive_oxygen + 2)

        # 산소 0 → 데미지
        if self.dive_oxygen <= 0 and self.dive_active:
            self.dive_damage_cd -= 1
            if self.dive_damage_cd <= 0:
                self.dive_damage_cd = 60
                self.health -= 5

    def update(self, keys, current_friction, mode, mouse_pos=None):
        self.mode = mode
        if self.combo_timer > 0: self.combo_timer -= 1
        else:
            if self.combo > 0: self.combo = max(0, self.combo - 1)
        if self.streak_timer > 0: self.streak_timer -= 1
        else: self.streak_kills = 0
        if self.dash_cd > 0: self.dash_cd -= 1
        if self.speed_boost > 0: self.speed_boost -= 1
        if self.overload_timer > 0: self.overload_timer -= 1
        
        # 스킬 타이머 업데이트
        if self.skill_dmg_timer > 0: self.skill_dmg_timer -= 1
        if self.skill_stealth_timer > 0: self.skill_stealth_timer -= 1
        if self.skill_vamp_timer > 0: self.skill_vamp_timer -= 1
        if self.skill_titan_timer > 0: self.skill_titan_timer -= 1
        if self.skill_gatling_timer > 0: self.skill_gatling_timer -= 1

        if self.form_morph_t < 1.0: self.form_morph_t = min(1.0, self.form_morph_t + 0.06)

        #  스킬 쿨타임 감소
        for sk in self.skill_cooldowns:
            if self.skill_cooldowns[sk] > 0:
                self.skill_cooldowns[sk] -= 1
                if sk == "izanagi" and self.skill_cooldowns[sk] == 0:
                    self.skill_izanagi_ready = True

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
        if self.skill_titan_timer > 0:
            self.invincible = max(self.invincible, 2) # 거인화 중 무적
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
        max_spd = SETTINGS.ship_max_speed * self.get_speed_mult()
        if self.vel.length() > max_spd:
            self.vel.scale_to_length(max_spd)
        self.world_pos += self.vel
        self._redraw()

    def _redraw(self):
        self.base_image.fill((0,0,0,0))
        is_titan = self.skill_titan_timer > 0
        sz = 80 if is_titan else 40
        if self.base_image.get_size() != (sz, sz):
            self.base_image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        
        form = SHIP_FORMS.get(self.ship_form, SHIP_FORMS["fighter"])
        t    = self.form_morph_t
        color_data = next((c for c in SHIP_COLORS if c["key"]==self.ship_color_key), SHIP_COLORS[0])

        if self.overload_timer > 0:
            # 과부하: 오렌지-적색 깜빡임
            pulse = int(200 + 55 * math.sin(self.overload_timer * 0.3))
            color = (pulse, pulse//3, 0)
        elif self.dash_timer > 0:
            color = (255,255,255)
        elif self.dive_active:
            # 잠수: 깊이에 따라 더 어두운 청색
            d_ratio = self.dive_depth / self.dive_max
            color = (0, int(80*(1-d_ratio)), int(180+75*d_ratio))
        elif self.abyss_mode:
            color = (0,200,255)
        else:
            color = color_data["color_p"] if self.dimension=="PHYSICAL" else color_data["color_v"]

        if self.mode == "SHIP":
            poly_curr = form["poly"]
            poly_prev = SHIP_FORMS.get(self.form_prev, form)["poly"]

            def lerp_poly(pa, pb, t):
                n = max(len(pa), len(pb))
                def ext(p, n):
                    return p + [p[-1]]*(n-len(p))
                pa2 = ext(pa, n); pb2 = ext(pb, n)
                return [(int(a[0]+(b[0]-a[0])*t), int(a[1]+(b[1]-a[1])*t))
                        for a, b in zip(pa2, pb2)]

            poly = lerp_poly(poly_prev, poly_curr, t)

            ship_frames = get_ship_image(self.ship_form, (sz*2, sz*2)) # Scale larger because extracted frames have lots of padding
            
            if ship_frames:
                speed_ratio = self.vel.length() / (SETTINGS.ship_max_speed * self.get_speed_mult() + 0.001)
                
                if self.dash_timer > 0:
                    frame_idx = len(ship_frames) - 1
                elif speed_ratio < 0.1:
                    frame_idx = 0
                elif speed_ratio < 0.4:
                    frame_idx = 1
                elif speed_ratio < 0.8:
                    frame_idx = 2
                else:
                    frame_idx = 3
                
                frame_idx = min(frame_idx, len(ship_frames)-1)
                ship_img = ship_frames[frame_idx]
                
                rect = ship_img.get_rect(center=(sz//2, sz//2))
                self.base_image.blit(ship_img, rect)
                
                # Draw colored outline to preserve form dimension tints
                pygame.draw.circle(self.base_image, color, (sz//2, sz//2), sz//2, 1)
            else:
                if len(poly) >= 3:
                    pygame.draw.polygon(self.base_image, color, poly)
                    pygame.draw.polygon(self.base_image, (255,255,255), poly, 1)

                eng_col = (0,200,255) if self.abyss_mode else (255,150,50)
                if self.dive_active:
                    eng_col = (0,120,255)
                for ep in form["engine_pos"]:
                    er = form["engine_r"]
                    pygame.draw.circle(self.base_image, eng_col, ep, er)
                    if self.speed_boost > 0:
                        pygame.draw.circle(self.base_image, (255,255,200), ep, er+2, 1)
                    # 과부하 엔진 이펙트
                    if self.overload_timer > 0:
                        pygame.draw.circle(self.base_image, (255,100,0), ep, er+3, 1)

                if self.ship_form == "dreadnought":
                    pygame.draw.rect(self.base_image, (200,50,50), (0,10,6,8))
                    pygame.draw.rect(self.base_image, (200,50,50), (34,10,6,8))
                if self.ship_form == "abyss_ship":
                    pygame.draw.circle(self.base_image, (0,150,255), (20,20), 18, 1)
                if self.ship_form == "phantom":
                    aura_col = (200,200,255) if self.dimension=="PHYSICAL" else (255,220,0)
                    pygame.draw.circle(self.base_image, aura_col, (20,20), 19, 1)

            #  잠수 기포 이펙트
            if self.dive_active and self.dive_depth > 10:
                for bx, by in [(8,8),(30,12),(15,30)]:
                    br = max(1, int(self.dive_depth / 30))
                    pygame.draw.circle(self.base_image, (100,200,255,120), (bx,by), br)

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

        #  과부하 외곽 링
        if self.overload_timer > 0:
            pulse = int(150 + 105 * math.sin(self.overload_timer * 0.4))
            pygame.draw.circle(self.base_image, (255, pulse//2, 0), (sz//2,sz//2), sz//2+1, 2)

        if is_titan:
            # 거인 오라
            pygame.draw.circle(self.base_image, (255, 50, 0, 100), (sz//2, sz//2), sz//2, 3)

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
        #  streak 카운트
        self.streak_kills += 1
        self.streak_timer  = 120
        return self.combo

    def take_hit(self, dmg):
        if self.invincible > 0 or self.dash_timer > 0 or self.skill_stealth_timer > 0:
            return 0
        if self.overload_timer > 0:
            return 0   #  과부하 중 무적
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
    def __init__(self, owner, drone_type="ATTACKER"):
        super().__init__()
        self.owner       = owner
        self.drone_type  = drone_type
        self.world_pos   = Vector2(owner.world_pos)
        self.orbit_angle = random.randint(0, 360)
        self.timer       = 0
        
        # 드론 타입별 설정
        # ATTACKER: 빠른 사격 (기본)
        # STRIKER: 강한 한방, 느린 사격
        # GUARD: 가까이서 방어형 사격
        self.stats = {
            "ATTACKER": {"cd": 22, "dmg": 0.8, "speed": 12, "orbit_r": 55,  "color": (0, 255, 200), "size": 18},
            "STRIKER":  {"cd": 55, "dmg": 2.5, "speed": 18, "orbit_r": 75,  "color": (255, 100, 50), "size": 24},
            "GUARD":    {"cd": 12, "dmg": 0.4, "speed": 10, "orbit_r": 35,  "color": (200, 255, 100), "size": 16},
        }.get(drone_type, {"cd": 22, "dmg": 0.8, "speed": 12, "orbit_r": 55, "color": (0, 255, 200), "size": 18})
        
        size = self.stats["size"]
        self.image       = pygame.Surface((size+4, size+4), pygame.SRCALPHA)
        self.rect        = self.image.get_rect()
        self._draw()

    def _draw(self):
        self.image.fill((0,0,0,0))
        c = self.stats["color"]; size = self.stats["size"]
        if self.drone_type == "STRIKER":
            # 중장갑형
            pygame.draw.rect(self.image, (180, 50, 50), (2, 4, size, size-6), border_radius=4)
            pygame.draw.circle(self.image, c, (size//2+2, size//2+2), 4)
        elif self.drone_type == "GUARD":
            # 신속방어형
            pygame.draw.circle(self.image, (80, 150, 100), (size//2+2, size//2+2), size//2)
            pygame.draw.circle(self.image, c, (size//2+2, size//2+2), 3)
        else:
            # 범용형
            pygame.draw.rect(self.image, (80, 180, 255), (3, 5, 16, 12))
            pygame.draw.circle(self.image, c, (9, 4), 2)
            pygame.draw.circle(self.image, c, (13, 4), 2)

    def update(self, enemies, projectiles, dimension, camera_offset):
        spd = 3.5 if self.drone_type == "GUARD" else 2.5
        self.orbit_angle = (self.orbit_angle + spd) % 360
        r = self.stats["orbit_r"]
        self.world_pos = self.owner.world_pos + Vector2(
            math.cos(math.radians(self.orbit_angle)) * r,
            math.sin(math.radians(self.orbit_angle)) * r,
        )
        sx = int(self.world_pos.x - camera_offset.x)
        sy = int(self.world_pos.y - camera_offset.y)
        self.rect.center = (sx, sy)
        self.timer += 1
        if self.timer >= self.stats["cd"]:
            self.timer = 0
            nearest, min_d = None, 450
            for e in enemies:
                if e.dimension_type == dimension:
                    d = (e.world_pos - self.world_pos).length()
                    if d < min_d:
                        min_d = d; nearest = e
            if nearest:
                d = nearest.world_pos - self.world_pos
                projectiles.add(Projectile(
                    self.world_pos, d.normalize(), dimension,
                    color_override=self.stats["color"], 
                    speed=self.stats["speed"], 
                    dmg=self.stats["dmg"], 
                    is_direction=True))


class ShadowSoldier(pygame.sprite.Sprite):
    def __init__(self, owner, world_pos, etype="basic_drone"):
        super().__init__()
        self.owner = owner
        self.world_pos = Vector2(world_pos)
        self.etype = etype
        data = ENEMY_DATA.get(etype, ENEMY_DATA["basic_drone"])
        sz = data["size"]
        self.image = pygame.Surface((sz, sz), pygame.SRCALPHA)
        # 그림자 효과 (검은색 + 보라색 라인)
        pygame.draw.circle(self.image, (20, 20, 20), (sz//2, sz//2), sz//2-1)
        pygame.draw.circle(self.image, (150, 0, 255), (sz//2, sz//2), sz//2-1, 2)
        self.rect = self.image.get_rect()
        self.timer = 0
        self.life = 900 # 15초
        self.speed = 4.5
        self.target = None

    def update(self, enemies, projectiles, dimension, camera_offset):
        self.life -= 1
        if self.life <= 0:
            self.kill()
            return

        # 가장 가까운 적 추적
        if not self.target or not self.target.alive():
            nearest, min_d = None, 600
            for e in enemies:
                if e.dimension_type == dimension:
                    d = (e.world_pos - self.world_pos).length()
                    if d < min_d:
                        min_d = d; nearest = e
            self.target = nearest

        if self.target:
            dir_to = (self.target.world_pos - self.world_pos).normalize()
            self.world_pos += dir_to * self.speed
        else:
            # 적이 없으면 주인 근처로
            dir_to = (self.owner.world_pos - self.world_pos)
            if dir_to.length() > 100:
                self.world_pos += dir_to.normalize() * self.speed

        self.timer += 1
        if self.timer % 40 == 0:
            if self.target and (self.target.world_pos - self.world_pos).length() < 350:
                d = self.target.world_pos - self.world_pos
                projectiles.add(Projectile(
                    self.world_pos, d.normalize(), dimension,
                    color_override=(180, 0, 255),
                    speed=10,
                    dmg=3,
                    is_direction=True,
                    size=6))

        sx = int(self.world_pos.x - camera_offset.x)
        sy = int(self.world_pos.y - camera_offset.y)
        self.rect.center = (sx, sy)


# ─────────────────────────────────────────
#  ENEMY DATA
# ─────────────────────────────────────────
ENEMY_DATA = {
    "basic_drone":   {"name":"기본 드론",  "hp":3.5, "speed":2.8, "size":24,"cp":(0,150,255),"cv":(50,50,200),"shape":"circle","behavior":"melee","gem":1},
    "swarm_organism":{"name":"군집 유기체","hp":1.8, "speed":3.5, "size":20,"cp":(80,200,80),"cv":(40,140,40),"shape":"triangle","behavior":"swarm","gem":1},
    "glitcher":      {"name":"글리처",     "hp":2.0, "speed":4.5, "size":20,"cp":(200,0,200),"cv":(255,0,255),"shape":"rect","behavior":"zigzag","gem":1},
    "hunter_drone":  {"name":"헌터 드론",  "hp":3.5, "speed":4.2, "size":22,"cp":(220,110,50),"cv":(160,50,0),"shape":"triangle","behavior":"melee","gem":1},
    "sentinel":      {"name":"감시자",     "hp":5.5, "speed":2.0, "size":26,"cp":(100,100,200),"cv":(50,50,120),"shape":"rect","behavior":"orbit","gem":2},
    "sniper_node":   {"name":"저격 노드",  "hp":4.0, "speed":1.2, "size":20,"cp":(255,255,100),"cv":(200,200,0),"shape":"diamond","behavior":"ranged","gem":2,"special":"ranged_shot"},
    "elite_enforcer":{"name":"엘리트",     "hp":9.5, "speed":3.2, "size":26,"cp":(220,50,50),"cv":(160,0,0),"shape":"rect","behavior":"hybrid","gem":3,"special":"armor"},
    "void_weaver":   {"name":"공허 방직자","hp":9.0, "speed":2.6, "size":28,"cp":(80,80,80),"cv":(0,220,220),"shape":"diamond","behavior":"orbit","gem":3,"special":"slow_field"},
    "corrupted_sentry":{"name":"오염된 센트리","hp":10.5,"speed":2.3,"size":28,"cp":(140,140,0),"cv":(0,255,0),"shape":"circle","behavior":"melee","gem":3,"special":"poison_on_death"},
    "shadow_lurker": {"name":"그림자 잠복자","hp":5.5, "speed":5.8, "size":22,"cp":(50,50,50),"cv":(10,10,10),"shape":"triangle","behavior":"zigzag","gem":3,"special":"dash"},
    "abyss_eel":     {"name":"심해 뱀장어","hp":7.5, "speed":3.8, "size":22,"cp":(0,100,150),"cv":(0,200,255),"shape":"triangle","behavior":"zigzag","gem":2,"special":"poison_on_death"},
    "depth_guardian":{"name":"심해 수호자","hp":14.0,"speed":1.6, "size":32,"cp":(0,60,120),"cv":(0,150,200),"shape":"rect","behavior":"orbit","gem":4,"special":"armor"},
    "leviathan_eye": {"name":"리바이어던의 눈","hp":25.0,"speed":1.1, "size":40,"cp":(0,40,100),"cv":(0,100,200),"shape":"circle","behavior":"ranged","gem":8,"special":"ranged_shot"},
    "null_fragment":  {"name":"공백 파편", "hp":2.2, "speed":6.8, "size":18,"cp":(180,180,200),"cv":(220,220,255),"shape":"diamond","behavior":"melee","gem":1},
    "void_titan":     {"name":"공허 타이탄","hp":35.0,"speed":1.8, "size":50,"cp":(60,0,120),"cv":(120,0,255),"shape":"circle","behavior":"orbit","gem":10,"special":"burst_shot"},
    "echo_phantom":   {"name":"에코 팬텀",  "hp":11.0,"speed":4.2, "size":26,"cp":(150,150,200),"cv":(200,100,255),"shape":"diamond","behavior":"zigzag","gem":3,"special":"dash"},
    "anomaly_core":        {"name":"이상 현상 코어","hp":55.0,"speed":1.4, "size":48,"cp":(100,160,220),"cv":(220,60,255),"shape":"circle","behavior":"orbit","gem":12,"special":"summon","spawn_progress":0.25},
    "dreadnought_construct":{"name":"드레드노트","hp":85.0,"speed":1.7, "size":58,"cp":(90,90,90),"cv":(160,0,0),"shape":"rect","behavior":"melee","gem":15,"special":"burst_shot","spawn_progress":0.50},
    "echo_wraith":         {"name":"메아리 망령","hp":65.0,"speed":3.4, "size":26,"cp":(130,130,160),"cv":(50,255,50),"shape":"diamond","behavior":"zigzag","gem":15,"special":"clone","spawn_progress":0.70},
    "abyss_leviathan":     {"name":"심연의 리바이어던","hp":140.0,"speed":1.2,"size":70,"cp":(0,50,120),"cv":(0,150,255),"shape":"circle","behavior":"orbit","gem":25,"special":"burst_shot","spawn_progress":0.55},
    "null_colossus":       {"name":"공백 거신","hp":105.0,"speed":2.1, "size":64,"cp":(100,100,140),"cv":(180,50,255),"shape":"rect","behavior":"melee","gem":20,"special":"phase_boss","spawn_progress":0.60},
    "nexus_overmind":  {"name":"넥서스 오버마인드","hp":260.0,"speed":1.4, "size":80,"cp":(180,180,210),"cv":(255,0,255),"shape":"circle","behavior":"orbit","gem":40,"special":"phase_boss","phase_count":3,"spawn_progress":0.85},
    "abyssal_tyrant":  {"name":"심연의 폭군","hp":350.0,"speed":2.0, "size":90,"cp":(80,0,0),"cv":(0,255,150),"shape":"circle","behavior":"melee","gem":50,"special":"phase_boss","phase_count":3,"spawn_progress":0.90},

    #  돌연변이 (Mutants)
    "mutant_drone":  {"name":"뮤턴트 드론", "hp":22.0,"speed":3.2,"size":30,"cp":(255,255,255),"cv":(255,0,255),"shape":"circle","behavior":"hybrid","gem":15,"special":"blink_dash","mutant":True},
    "mutant_sentinel":{"name":"뮤턴트 파수꾼","hp":38.0,"speed":2.4,"size":35,"cp":(0,255,100),"cv":(0,200,50),"shape":"rect","behavior":"hybrid","gem":20,"special":"energy_beam","mutant":True},
    "mutant_lurker": {"name":"뮤턴트 복수자","hp":18.0,"speed":4.0,"size":28,"cp":(255,100,0),"cv":(200,50,0),"shape":"triangle","behavior":"melee","gem":18,"special":"dash_attack","mutant":True},
    "mutant_void":   {"name":"뮤턴트 보이더","hp":30.0,"speed":1.2,"size":40,"cp":(150,0,255),"cv":(100,0,200),"shape":"diamond","behavior":"ranged","gem":22,"special":"spiral_shot","mutant":True},

    "gravity_orb":   {"name":"중력 구체",   "hp":11.5,"speed":0.92,"size":30, "cp":(150,0,255), "cv":(100,0,200), "shape":"circle", "behavior":"melee", "gem":5, "special":"pull_player"},
    "beam_turret":   {"name":"빔 터렛",     "hp":15.4,"speed":0,   "size":32, "cp":(255,50,50), "cv":(200,0,0),   "shape":"rect",   "behavior":"ranged", "gem":10, "special":"constant_laser"},
    "plasma_fly":    {"name":"플라즈마 파리","hp":1.5, "speed":4.98,"size":16, "cp":(255,255,0), "cv":(200,200,50),"shape":"triangle", "behavior":"zigzag","gem":2},
    "dark_matter":   {"name":"암흑 물질",   "hp":30.7,"speed":1.38,"size":45, "cp":(20,20,20),  "cv":(50,0,80),   "shape":"circle", "behavior":"swarm", "gem":15, "special":"split_on_death"},
    "void_stinger":  {"name":"보이드 침입자","hp":7.7, "speed":4.21,"size":24, "cp":(0,255,255), "cv":(0,150,150), "shape":"diamond", "behavior":"melee", "gem":6,  "special":"dash_attack"},
    "void_god":        {"name":"공허의 신","hp":287.5,"speed":1.15,"size":100,"cp":(60,0,120),"cv":(255,200,255),"shape":"circle","behavior":"orbit","gem":60,"special":"phase_boss","phase_count":4,"spawn_progress":0.88},
    "abyss_sovereign": {"name":"심연의 군주","hp":345.0,"speed":0.81,"size":110,"cp":(0,30,80),"cv":(0,200,255),"shape":"circle","behavior":"melee","gem":70,"special":"phase_boss","phase_count":4,"spawn_progress":0.92},
    "rift_guardian":   {"name":"균열의 수호자","hp":138.0,"speed":1.72,"size":80,"cp":(120,0,180),"cv":(255,50,255),"shape":"circle","behavior":"orbit","gem":30,"special":"phase_boss","phase_count":3},
    "rift_devourer":   {"name":"균열의 포식자","hp":184.0,"speed":1.60,"size":86,"cp":(200,0,100),"cv":(255,100,0),"shape":"triangle","behavior":"melee","gem":35,"special":"phase_boss","phase_count":3},
    "rift_colossus":   {"name":"균열의 거신",  "hp":230.0,"speed":1.15,"size":100,"cp":(80,80,200),"cv":(200,200,255),"shape":"rect","behavior":"orbit","gem":40,"special":"phase_boss","phase_count":4},
    "void_wraith_king":{"name":"공허 망령왕",  "hp":161.0,"speed":3.22,"size":76,"cp":(50,0,100),"cv":(200,50,255),"shape":"diamond","behavior":"zigzag","gem":32,"special":"phase_boss","phase_count":3},
    "abyss_rift_lord": {"name":"심연 균열군주","hp":276.0,"speed":0.92,"size":110,"cp":(0,20,80),"cv":(0,150,255),"shape":"circle","behavior":"ranged","gem":50,"special":"phase_boss","phase_count":4},
    "entropy_core":    {"name":"엔트로피 코어","hp":207.0,"speed":1.84,"size":90,"cp":(200,100,0),"cv":(255,200,50),"shape":"circle","behavior":"orbit","gem":38,"special":"phase_boss","phase_count":3},
    "deep_angler":     {"name":"심해 아귀",  "hp":6.9, "speed":2.07,"size":30,"cp":(20,60,100),"cv":(0,180,255),"shape":"circle","behavior":"ranged","gem":4,"special":"ranged_shot"},
    "abyss_hydra":     {"name":"심연 히드라","hp":28.75,"speed":1.38,"size":50,"cp":(0,40,120),"cv":(0,120,200),"shape":"rect","behavior":"orbit","gem":12,"special":"burst_shot","spawn_progress":0.40},
    "colossal_titan":  {"name":"초대형 거인","hp":500.0,"speed":0.70,"size":130,"cp":(220,50,50),"cv":(180,0,0),"shape":"rect","behavior":"melee","gem":100, "special":"steam_burst", "spawn_progress":0.95},
    "blink_striker":   {"name":"블링크 스트라이커","hp":12.0,"speed":3.50,"size":24,"cp":(0,255,150),"cv":(200,255,255),"shape":"triangle","behavior":"melee","gem":8, "special":"blink_dash"},
    "energy_cursed":   {"name":"주령 구체","hp":45.0,"speed":1.20,"size":40,"cp":(50,0,80),"cv":(150,0,255),"shape":"circle","behavior":"hybrid","gem":20, "special":"energy_beam"},
    "gravity_core":    {"name":"중력 코어","hp":80.0,"speed":0.80,"size":50,"cp":(30,30,30),"cv":(0,0,0),"shape":"circle","behavior":"melee","gem":25, "special":"gravity_vacuum"},
    "spiral_master":   {"name":"나선 마스터","hp":60.0,"speed":1.50,"size":45,"cp":(0,100,200),"cv":(200,255,255),"shape":"triangle","behavior":"ranged","gem":22, "special":"spiral_shot"},
    # ── 유니버스 전용 엘리트 적 ──
    "cyber_enforcer":  {"name":"사이버 집행자", "hp":14.0,"speed":4.2,"size":28,"cp":(255,255,0),"cv":(200,200,0), "shape":"diamond","behavior":"ranged","gem":8,  "special":"ranged_shot"},
    "abyss_specter":   {"name":"심연 유령",     "hp":20.0,"speed":1.8,"size":32,"cp":(120,0,200),"cv":(80,0,140),  "shape":"circle", "behavior":"zigzag","gem":10, "special":"blink_dash"},
    "golden_golem":    {"name":"황금 골렘",     "hp":35.0,"speed":0.9,"size":40,"cp":(255,200,50),"cv":(200,150,0),"shape":"rect",   "behavior":"melee", "gem":22, "special":"armor"},
    "glitch_ghost":    {"name":"글리치 유령",   "hp":9.0, "speed":5.0,"size":24,"cp":(255,60,180),"cv":(200,0,140),"shape":"diamond","behavior":"zigzag","gem":7,  "special":"dash"},
    # ── 행성 전용 적 (Island Enemies) ──
    "marine_soldier":  {"name":"해군 병사",  "hp":6.0,  "speed":3.0, "size":24,"cp":(255,255,255),"cv":(200,200,255),"shape":"circle","behavior":"melee","gem":2},
    "marine_officer":  {"name":"해군 장교",  "hp":15.0, "speed":2.5, "size":28,"cp":(0,50,150),  "cv":(50,100,255), "shape":"rect",  "behavior":"ranged","gem":5, "special":"ranged_shot"},
    "marine_ship":     {"name":"해군 함선",  "hp":45.0, "speed":1.5, "size":45,"cp":(50,50,60),   "cv":(100,100,120),"shape":"rect",  "behavior":"ranged","gem":15, "special":"burst_shot"},
    "samurai_ronin":   {"name":"떠돌이 무사","hp":12.0, "speed":4.0, "size":24,"cp":(150,50,50), "cv":(200,80,80),  "shape":"triangle","behavior":"zigzag","gem":4, "special":"dash"},
    "samurai_general": {"name":"사무라이 장군","hp":110.0, "speed":2.0, "size":42,"cp":(100,0,0),   "cv":(150,20,20),  "shape":"rect",  "behavior":"melee","gem":25, "special":"armor", "dropped_weapon": "void_blade"},
    "desert_bandit":   {"name":"사막 도적",  "hp":8.0,  "speed":3.8, "size":22,"cp":(210,180,100),"cv":(180,150,80), "shape":"triangle","behavior":"chase","gem":3},
    "sand_worm":       {"name":"샌드 웜",    "hp":25.0, "speed":1.8, "size":35,"cp":(150,100,50), "cv":(100,70,30),  "shape":"circle","behavior":"melee","gem":12, "special":"gravity_vacuum"},
    "sky_guardian":    {"name":"하늘 파수꾼","hp":18.0, "speed":3.5, "size":26,"cp":(200,240,255),"cv":(100,150,255),"shape":"diamond","behavior":"ranged","gem":10, "special":"ranged_shot"},
    "storm_bird":      {"name":"뇌조",       "hp":10.0, "speed":5.5, "size":20,"cp":(255,255,100),"cv":(200,200,50), "shape":"triangle","behavior":"zigzag","gem":6,  "special":"dash_attack"},
    "nexus_overmind":  {"name":"넥서스 오버마인드", "hp":400.0, "speed":1.0, "size":120, "cp":(0,255,255), "cv":(255,0,255), "shape":"circle", "behavior":"orbit", "gem":150, "special":"phase_boss", "dropped_weapon":"omega_ray"},
    "abyssal_tyrant":  {"name":"심연의 폭군", "hp":500.0, "speed":0.8, "size":140, "cp":(50,0,100), "cv":(0,50,150), "shape":"rect", "behavior":"melee", "gem":200, "special":"phase_boss", "dropped_weapon":"thunder_spear"},
}
# ─────────────────────────────────────────
#  JOB DATA (전직 시스템)
# ─────────────────────────────────────────
JOB_DATA = {
    "전사": {
        "name": "전사", "color": (220, 80, 60),
        "desc": "근접 전투의 달인. 두꺼운 장갑으로 전선을 지킨다.",
        "req_label": "근접 처치",
        "buff": "최대 HP +35% · 데미지 +20%",
        "nerf": "이동속도 -15%",
        "hp_mult": 1.35, "dmg_mult": 1.20, "speed_mult": 0.85,
        "shield_mult": 1.0, "cd_mult": 1.0,
    },
    "저격수": {
        "name": "저격수", "color": (80, 220, 255),
        "desc": "먼 거리에서 치명적인 일격을 날린다.",
        "req_label": "원거리 처치",
        "buff": "데미지 +50% · 탄속 +25%",
        "nerf": "이동속도 -20% · HP -10%",
        "hp_mult": 0.90, "dmg_mult": 1.50, "speed_mult": 0.80,
        "shield_mult": 1.0, "cd_mult": 1.0,
    },
    "파일럿": {
        "name": "파일럿", "color": (100, 255, 180),
        "desc": "초월적 기동성으로 전장을 누빈다.",
        "req_label": "대쉬 횟수",
        "buff": "이동속도 +30% · 대쉬 쿨타임 -35%",
        "nerf": "데미지 -15%",
        "hp_mult": 1.0, "dmg_mult": 0.85, "speed_mult": 1.30,
        "shield_mult": 1.0, "cd_mult": 0.65,
    },
    "마법사": {
        "name": "마법사", "color": (180, 80, 255),
        "desc": "스킬의 힘을 극한까지 끌어올린다.",
        "req_label": "스킬 사용",
        "buff": "스킬 쿨타임 -40% · 스킬 데미지 +50%",
        "nerf": "최대 HP -20%",
        "hp_mult": 0.80, "dmg_mult": 1.0, "speed_mult": 1.0,
        "shield_mult": 1.0, "cd_mult": 1.0,
        "skill_cd_mult": 0.60, "skill_dmg_mult": 1.50,
    },
    "흡혈귀": {
        "name": "흡혈귀", "color": (180, 0, 80),
        "desc": "적의 피를 마셔 상처를 치유한다.",
        "req_label": "흡혈 처치",
        "buff": "처치 시 체력 회복 +3 · HP +25%",
        "nerf": "쉴드 없음",
        "hp_mult": 1.25, "dmg_mult": 1.0, "speed_mult": 1.0,
        "shield_mult": 0.0, "cd_mult": 1.0,
        "lifesteal_bonus": 3,
    },
    "기계공": {
        "name": "기계공", "color": (200, 180, 80),
        "desc": "무기 운용의 달인. 모든 무기를 최적화한다.",
        "req_label": "무기 전환",
        "buff": "전체 데미지 +15% · 사격속도 +20%",
        "nerf": "이동속도 -10%",
        "hp_mult": 1.0, "dmg_mult": 1.15, "speed_mult": 0.90,
        "shield_mult": 1.0, "cd_mult": 0.80,
    },
    "탱커": {
        "name": "탱커", "color": (100, 100, 200),
        "desc": "강철 같은 방어력으로 모든 공격을 버텨낸다.",
        "req_label": "피해 받음",
        "buff": "최대 HP +60% · 쉴드 +100%",
        "nerf": "이동속도 -30%",
        "hp_mult": 1.60, "dmg_mult": 1.0, "speed_mult": 0.70,
        "shield_mult": 2.0, "cd_mult": 1.0,
    },
    "광속": {
        "name": "광속", "color": (255, 230, 80),
        "desc": "빛보다 빠르게 움직인다. 회피가 곧 공격이다.",
        "req_label": "대쉬 횟수",
        "buff": "이동속도 +55% · 대쉬 2연속",
        "nerf": "HP -25% · 데미지 -20%",
        "hp_mult": 0.75, "dmg_mult": 0.80, "speed_mult": 1.55,
        "shield_mult": 1.0, "cd_mult": 0.50,
        "double_dash": True,
    },
    "차원술사": {
        "name": "차원술사", "color": (0, 200, 255),
        "desc": "차원의 경계를 자유로이 오간다.",
        "req_label": "차원 전환",
        "buff": "공허 데미지 +70% · 차원 면역",
        "nerf": "물질계 데미지 -10%",
        "hp_mult": 1.0, "dmg_mult": 0.90, "speed_mult": 1.0,
        "shield_mult": 1.10, "cd_mult": 1.0,
        "void_dmg_mult": 1.70, "void_immune": True,
    },
    "학살자": {
        "name": "학살자", "color": (255, 100, 0),
        "desc": "피와 광기로 전장을 물든다. 콤보가 힘이다.",
        "req_label": "최고 콤보",
        "buff": "콤보 보너스 2배 · 5킬마다 속도 +5%",
        "nerf": "쉴드 없음 · HP -15%",
        "hp_mult": 0.85, "dmg_mult": 1.0, "speed_mult": 1.0,
        "shield_mult": 0.0, "cd_mult": 1.0,
        "combo_mult_bonus": 2.0,
    },
}

# ─────────────────────────────────────────
#  JOB TIER SYSTEM
# ─────────────────────────────────────────
JOB_TIER_DATA = {
    "names":  ["초급", "중급", "고급", "전설", "신화"],
    "colors": [(180, 180, 180), (80, 220, 80), (80, 150, 255), (255, 200, 0), (220, 100, 255)],
    "kills":  [0, 100, 300, 700, 1500],   # 해당 등급 도달에 필요한 직업 처치 수
    "dmg_mult": [1.0, 1.15, 1.35, 1.65, 2.20],  # _job_tier_mult 값
}

# ─────────────────────────────────────────
#  JOB SHRINE (월드 오브젝트)
# ─────────────────────────────────────────
class JobShrine:
    """전직 신전 — 클릭 시 재전직 UI 표시"""
    WORLD_POS      = Vector2(1400, 0)
    INTERACT_RANGE = 160

    def __init__(self):
        self.world_pos = Vector2(self.WORLD_POS)
        self._t = 0

    def update(self):
        self._t += 1

    def draw(self, surface, camera_offset):
        sx = int(self.world_pos.x - camera_offset.x)
        sy = int(self.world_pos.y - camera_offset.y)
        if not (-80 <= sx <= 880 and -80 <= sy <= 680):
            return
        t = self._t
        pulse = 0.5 + 0.5 * math.sin(t * 0.04)
        # 외곽 글로우 링
        glow_r = int(38 + 10 * pulse)
        pygame.draw.circle(surface, (40, 0, 90), (sx, sy), glow_r)
        # 회전하는 6개 오브
        for i in range(6):
            angle = math.radians(t * 1.8 + i * 60)
            ox = int(math.cos(angle) * 28)
            oy = int(math.sin(angle) * 28)
            c = (int(130 + 125 * pulse), int(60 + 40 * pulse), 255)
            pygame.draw.circle(surface, c, (sx + ox, sy + oy), 5)
        # 코어
        pygame.draw.circle(surface, (90, 0, 180), (sx, sy), 20)
        pygame.draw.circle(surface, (int(180 + 75 * pulse), 100, 255), (sx, sy), 12)
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 5)
        pygame.draw.circle(surface, (180, 100, 255), (sx, sy), 20, 2)
        # 지면 마커 (별 4개)
        for angle_deg in (0, 90, 180, 270):
            ang = math.radians(angle_deg + t * 0.8)
            mx2 = sx + int(math.cos(ang) * 44)
            my2 = sy + int(math.sin(ang) * 44)
            pygame.draw.circle(surface, (120, 60, 200), (mx2, my2), 3)

    def in_range(self, player_world_pos):
        return (player_world_pos - self.world_pos).length() <= self.INTERACT_RANGE

    def screen_rect(self, camera_offset):
        sx = int(self.world_pos.x - camera_offset.x)
        sy = int(self.world_pos.y - camera_offset.y)
        return pygame.Rect(sx - 28, sy - 28, 56, 56)

# ─────────────────────────────────────────
#  PLANET (ISLANDS)
# ─────────────────────────────────────────
class Planet(pygame.sprite.Sprite):
    def __init__(self, world_pos, ptype="marine", size=250):
        super().__init__()
        self.world_pos = Vector2(world_pos)
        self.ptype = ptype
        self.size = size
        self.angle = 0
        self.rotate_speed = random.uniform(0.01, 0.05)
        
        # 행성 타입별 색상 설정
        self.data = {
            "marine":  {"color": (0, 100, 255), "atmo": (100, 200, 255, 40), "name": "해군 지부 행성"},
            "desert":  {"color": (210, 180, 100), "atmo": (255, 200, 50, 40), "name": "사막 행성 알라바스타"},
            "sky":     {"color": (200, 240, 255), "atmo": (255, 255, 255, 60), "name": "하늘 행성 스카이피아"},
            "samurai": {"color": (80, 20, 20), "atmo": (200, 50, 50, 40), "name": "사무라이 행성 와노쿠니"},
            "job":     {"color": (150, 0, 255), "atmo": (200, 100, 255, 50), "name": "전직의 성소"},
        }.get(ptype, {"color": (100, 100, 100), "atmo": (150, 150, 150, 30), "name": "미개척 행성"})

        self.image = pygame.Surface((size*2 + 40, size*2 + 40), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self._draw()

    def _draw(self):
        self.image.fill((0,0,0,0))
        c = self.world_pos
        center = (self.size + 20, self.size + 20)
        
        # 1. 대기권 (Atmosphere)
        atmo_col = self.data["atmo"]
        pygame.draw.circle(self.image, atmo_col, center, self.size + 15)
        
        # 2. 행성 본체
        base_col = self.data["color"]
        pygame.draw.circle(self.image, base_col, center, self.size)
        
        # 3. 디테일 (크레이터/구름 등)
        for i in range(5):
            angle = math.radians(i * 72)
            ox = int(math.cos(angle) * (self.size * 0.6))
            oy = int(math.sin(angle) * (self.size * 0.6))
            pygame.draw.circle(self.image, (max(0, base_col[0]-40), max(0, base_col[1]-40), max(0, base_col[2]-40), 100), 
                               (center[0]+ox, center[1]+oy), self.size // 4)

    def update(self):
        self.angle += self.rotate_speed

    def update_screen_pos(self, camera_offset):
        sx = int(self.world_pos.x - camera_offset.x)
        sy = int(self.world_pos.y - camera_offset.y)
        self.rect.center = (sx, sy)

    def draw(self, surface, camera_offset):
        self.update_screen_pos(camera_offset)
        # 화면 밖이면 그리지 않음
        if not surface.get_rect().colliderect(self.rect.inflate(100, 100)):
            return
        surface.blit(self.image, self.rect)
        
        # 행성 이름 텍스트 표시 (가까이 가면 보임)
        dist = (self.world_pos - (camera_offset + Vector2(400, 300))).length()
        if dist < 1200:
            alpha = max(0, min(255, int(255 * (1 - (dist - 400) / 800))))
            # 텍스트는 엔진에서 렌더링하도록 하거나 여기서 임시로 그림
            pass


# ─────────────────────────────────────────
#  COMBAT OVERHAUL: WEAK POINT
# ─────────────────────────────────────────
class WeakPoint:
    def __init__(self, size):
        self.offset = Vector2(random.randint(-size//4, size//4), random.randint(-size//4, size//4))
        self.timer = 0
        self.visible = True

    def update(self, size):
        self.timer += 1
        if self.timer % 120 == 0: # 2초마다 위치 변경
            self.offset = Vector2(random.randint(-size//3, size//3), random.randint(-size//3, size//3))

    def check_hit(self, hit_pos, center_pos):
        return (hit_pos - (center_pos + self.offset)).length() < 15


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
        self.difficulty = difficulty
        self.speed     = data["speed"] * (1 + difficulty * 0.25)   # ↑ 0.18→0.25
        self.hp        = int(data["hp"] * (1 + difficulty * 0.38)) # ↑ 0.25→0.38
        self.max_hp    = self.hp
        self.dmg_bonus = int(difficulty * 2.0)                      # ↑ 1.2→2.0
        self.gem_val   = data.get("gem",1)
        self.special   = data.get("special",None)
        self.behavior  = data["behavior"]
        self.name      = data["name"]
        self.is_mutant = data.get("mutant", False)
        self.enraged   = False  # 30% HP 이하 분노 상태
        self.special_timer = 0
        self.flash_timer = 0
        self.phase     = 1
        self.orbit_angle = random.uniform(0,360)
        
        #  약점 시스템 (보스급 전용)
        self.weak_point = None
        if self.max_hp >= 100 or self.special == "phase_boss":
            self.weak_point = WeakPoint(sz)
            
        #  Echo Shot 히스토리 추적 (COMBAT OVERHAUL TYPE-1)
        self.pos_history = []
        self.multiverse_type = "PRIME"
        self.dropped_weapon = data.get("dropped_weapon", None)

        # 유니버스 인챈트 시스템
        self.enchant = None  # "overcharged"|"shadowed"|"gilded"|"glitched"

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
            pygame.draw.circle(self.image, (min(255,cp[0]+60), min(255,cp[1]+60), min(255,cp[2]+60)), (cx,cy), r//2) # 코어 광원
            if data["hp"] >= 20: 
                pygame.draw.circle(self.image, (255,200,0), (cx,cy), r, 3)
            elif data["hp"] >= 5: 
                pygame.draw.circle(self.image, white, (cx,cy), r, 1)
        elif shape == "triangle":
            pygame.draw.polygon(self.image, cp, [(cx,2),(sz-2,sz-2),(2,sz-2)])
            pygame.draw.circle(self.image, white, (cx, cy+2), 3) # 중심 램프
        elif shape == "rect":
            pygame.draw.rect(self.image, cp, (2,2,sz-4,sz-4))
            pygame.draw.rect(self.image, white, (2,2,sz-4,sz-4), 1)
            pygame.draw.rect(self.image, (min(255,cp[0]*2), min(255,cp[1]*2), min(255,cp[2]*2)), (cx-2,cy-2,4,4)) # 중앙 센서
            if data["hp"] >= 5: pygame.draw.rect(self.image, (255,200,0),(2,2,sz-4,sz-4), 2)
        elif shape == "diamond":
            pygame.draw.polygon(self.image, cp, [(cx,2),(sz-2,cy),(cx,sz-2),(2,cy)])
            pygame.draw.polygon(self.image, white, [(cx,2),(sz-2,cy),(cx,sz-2),(2,cy)], 1)
            pygame.draw.circle(self.image, white, (cx,cy), 3) # 다이아몬드 코어

        #  약점 표시 (보라색 원형 코어)
        if self.weak_point:
            wx, wy = cx + self.weak_point.offset.x, cy + self.weak_point.offset.y
            pygame.draw.circle(self.image, (255, 255, 255), (int(wx), int(wy)), 8, 1)
            pygame.draw.circle(self.image, (255, 0, 0, 150), (int(wx), int(wy)), 5)
            
        if self.is_mutant:
            # 돌연변이 전용 테두리 및 코어 효과
            pygame.draw.circle(self.image, (255, 255, 255, 120), (cx, cy), r+1, 2)
            pygame.draw.circle(self.image, cp, (cx, cy), 5)

        if self.special == "phase_boss" and self.phase >= 2:
            pygame.draw.circle(self.image, (255,50,50), (cx,cy), r, 3)

        # 분노(Enrage) 시각 표시 — 붉은 맥동 링
        if getattr(self, "enraged", False):
            pygame.draw.rect(self.image, (255, 30, 30), (0, 0, sz, sz), 3, border_radius=4)
            pygame.draw.rect(self.image, (255, 120, 0), (1, 1, sz-2, sz-2), 1, border_radius=3)

        # 인챈트 시각 표시 — 외곽 광원 링
        if self.enchant:
            ec = {
                "overcharged": (255, 255, 0),
                "shadowed":    (160, 0, 255),
                "gilded":      (255, 200, 50),
                "glitched":    (255, 50, 160),
            }.get(self.enchant, (255, 255, 255))
            # 얇은 이중 링으로 표시 (파티클보다 가벼움)
            pygame.draw.rect(self.image, ec, (0, 0, sz, sz), 2, border_radius=5)
            # 코너 마킹
            for px, py in [(2,2),(sz-4,2),(2,sz-4),(sz-4,sz-4)]:
                pygame.draw.rect(self.image, (255,255,255), (px, py, 3, 3))

    def update_screen_pos(self, camera_offset):
        sx = int(self.world_pos.x - camera_offset.x)
        sy = int(self.world_pos.y - camera_offset.y)
        self.rect.center = (sx,sy)

    def update(self, player_world_pos, enemy_projectiles=None, dimension=None, all_enemies=None):
        self.special_timer += 1
        if self.weak_point: self.weak_point.update(self.rect.width) #  약점 동기화
        
        #  히스토리 기록 (Echo Shot 용)
        self.pos_history.append(Vector2(player_world_pos))
        if len(self.pos_history) > 60: self.pos_history.pop(0)
        
        self._do_behavior(player_world_pos, all_enemies)
        if enemy_projectiles is not None and dimension is not None:
            self._try_shoot(player_world_pos, enemy_projectiles, dimension)
        self.pos = self.world_pos

    def _try_shoot(self, player_pos, eprojs, dimension):
        if self.dimension_type != dimension: return

        diff = getattr(self, "difficulty", 1.0)

        #  멀티버스 연사속도 보정 (CYBER: 30% 더 자주 발사)
        rate_mult = 0.7 if self.multiverse_type == "CYBER" else 1.0
        # 분노 상태: 발사 간격 추가 단축
        if getattr(self, "enraged", False): rate_mult *= 0.65

        # 난이도 기반 발사체 속도 보너스 (최대 +5)
        spd_bonus = min(5.0, diff * 0.45)

        d_vec = player_pos - self.world_pos
        dist  = d_vec.length()

        ranged_interval = max(35, int(90 * rate_mult - diff * 3))
        if self.special == "ranged_shot" and self.special_timer % ranged_interval == 0 and dist < 550:
            eprojs.add(EnemyProjectile(self.world_pos, d_vec.normalize(), dimension,
                                       color=(255,255,0), speed=6 + spd_bonus, dmg=8 + self.dmg_bonus))

        burst_interval = max(40, int(80 * rate_mult - diff * 2.5))
        if self.special == "burst_shot" and self.special_timer % burst_interval == 0:
            for a in range(0,360,45):
                v = Vector2(math.cos(math.radians(a)), math.sin(math.radians(a)))
                eprojs.add(EnemyProjectile(self.world_pos, v, dimension,
                                           color=(255,80,0), speed=5 + spd_bonus * 0.6, dmg=5 + self.dmg_bonus))

        phase_interval = max(35, int(60 - diff * 2))
        if self.special == "phase_boss" and self.special_timer % phase_interval == 0:
            angle_step = max(30, 90 - self.phase * 15)  # 페이즈 오를수록 더 많은 탄
            for a in range(0, 360, angle_step):
                v = Vector2(math.cos(math.radians(a + self.special_timer)), math.sin(math.radians(a + self.special_timer)))
                eprojs.add(EnemyProjectile(self.world_pos, v, dimension,
                                           color=(255,0,100), speed=4+self.phase+spd_bonus*0.5,
                                           dmg=8+self.phase*3 + self.dmg_bonus))

        if self.special == "steam_burst" and self.special_timer % max(90, 150 - int(diff*4)) == 0:
            for a in range(0,360,15):
                v = Vector2(math.cos(math.radians(a)), math.sin(math.radians(a)))
                eprojs.add(EnemyProjectile(self.world_pos, v, dimension,
                                           color=(200,200,200), speed=3 + spd_bonus * 0.4, dmg=15 + self.dmg_bonus))

        if self.special == "energy_beam" and self.special_timer % max(70, 120 - int(diff*4)) == 0:
            v = (player_pos - self.world_pos).normalize()
            for i in range(5):
                pos = self.world_pos + v * (i * 20)
                eprojs.add(EnemyProjectile(pos, v, dimension,
                                           color=(150,0,255), speed=10 + spd_bonus * 0.5, dmg=12 + self.dmg_bonus))

        if self.special == "spiral_shot" and self.special_timer % max(45, 80 - int(diff*3)) == 0:
            for a in range(0, 360, 45):
                angle_rad = math.radians(a + self.special_timer * 2)
                v = Vector2(math.cos(angle_rad), math.sin(angle_rad))
                eprojs.add(EnemyProjectile(self.world_pos, v, dimension,
                                           color=(0, 255, 255), speed=5 + spd_bonus * 0.5, dmg=7 + self.dmg_bonus))

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
        elif self.behavior == "snipe" or self.behavior == "ranged":
            if dist > 350:   self.vel = chase_dir * self.speed
            elif dist < 200: self.vel = -chase_dir * self.speed
            else:            self.vel *= 0.9
        elif self.behavior == "melee":
            self.vel = chase_dir * self.speed
        elif self.behavior == "hybrid":
            # 거리에 따라 다르게 행동 (적정 거리 250~350)
            if dist > 400:   self.vel = chase_dir * self.speed
            elif dist < 200: self.vel = -chase_dir * self.speed
            else:
                # 적정 거리에서 플레이어 주위를 조금씩 흔들며 이동
                perp = Vector2(-chase_dir.y, chase_dir.x)
                self.vel = (perp * math.sin(self.special_timer * 0.05)).normalize() * (self.speed * 0.5)
            
            # 하이브리드는 가끔 돌격 스킬 사용
            if self.special_timer % 200 == 0 and dist < 450:
                self.vel = chase_dir * self.speed * 4
        if self.special == "dash" and self.special_timer % 120 == 0:
            self.vel = chase_dir * self.speed * 5
        if self.special == "blink_dash" and self.special_timer % 90 == 0:
            if dist < 400:
                self.world_pos += chase_dir * 150 # 텔레포트형 이동
        if self.special == "gravity_vacuum" and dist < 500:
            # 주위 개체 및 플레이어를 끌어당김 (가상으로 속도 조절)
            pass # engine.py에서 플레이어 위치 조정 필요

        # 글리치 인챈트: 랜덤 순간이동
        if self.enchant == "glitched" and self.special_timer % 80 == 0:
            self.world_pos += Vector2(random.uniform(-90, 90), random.uniform(-90, 90))

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

    def apply_enchant(self, enchant_type):
        """유니버스 전환 시 적에게 인챈트 부여"""
        old = self.enchant
        self.enchant = enchant_type
        # 이전 인챈트의 stat 변형은 누적 방지를 위해 원본 기반으로 처리
        base_speed = ENEMY_DATA.get(self.etype, {}).get("speed", self.speed)
        if enchant_type == "overcharged":
            self.speed = base_speed * 1.45
        elif enchant_type == "shadowed":
            if old != "shadowed":  # 중복 적용 방지
                boost = int(self.max_hp * 0.55)
                self.hp   = min(self.hp + boost, self.max_hp + boost)
                self.max_hp += boost
                self.dmg_bonus += 4
        elif enchant_type == "gilded":
            self.gem_val = int(ENEMY_DATA.get(self.etype, {}).get("gem", 1) * 2.5)
            self.speed   = base_speed * 1.20
        elif enchant_type == "glitched":
            self.speed = base_speed * 0.95  # 약간 느리지만 텔레포트
        else:  # None (PRIME — 인챈트 해제)
            self.speed    = base_speed
            self.gem_val  = ENEMY_DATA.get(self.etype, {}).get("gem", 1)
        self._draw()

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
        self.flash_timer = 3  # 피격 시 3프레임 동안 흰색으로 번쩍임
        # ── 분노(Enrage): HP 30% 이하에서 폭주 ──
        if (not self.enraged and self.hp > 0
                and self.special != "phase_boss"
                and self.hp < self.max_hp * 0.3):
            self.enraged = True
            self.speed  *= 1.7
            self.dmg_bonus += 5
            self._draw()   # 빨간 테두리 재그리기
        return self.hp <= 0


# ─────────────────────────────────────────
#  PROJECTILE (player)
# ─────────────────────────────────────────
class Projectile(pygame.sprite.Sprite):
    def __init__(self, world_pos, direction, dimension,
                 game=None, color_override=None, speed=8, dmg=1, is_direction=True, size=5):
        super().__init__()
        self.game = game
        self.dimension = dimension
        self.dmg       = dmg
        self.world_pos = Vector2(world_pos)
        sz = max(size,4)*3
        self.image = pygame.Surface((sz,sz), pygame.SRCALPHA)
        color = color_override or ((0,255,255) if dimension=="PHYSICAL" else (255,0,255))
        r = sz//2
        # 글로우 효과를 위해 겹쳐 그리기
        pygame.draw.circle(self.image, (*color, 60), (r,r), r-1)
        pygame.draw.circle(self.image, (*color, 150), (r,r), r-3)
        pygame.draw.circle(self.image, (255,255,255), (r,r), max(1,r-5))
        self.rect = self.image.get_rect()
        self.vel  = Vector2(direction).normalize()*speed if Vector2(direction).length()>0 else Vector2(0,-speed)
        self.life = 0
        
        #  멀티버스 특수 효과 (GLITCH: 관통 확률 부여)
        self.pierce = False
        if getattr(self, "multiverse_type", "PRIME") == "GLITCH":
            if random.random() < 0.4: self.pierce = True

    def update_screen_pos(self, camera_offset):
        self.rect.center = (int(self.world_pos.x-camera_offset.x),
                            int(self.world_pos.y-camera_offset.y))

    def update(self):
        # ★ 실존 우주 이론: 중력 렌즈 & 인력 (Gravitational Lensing)
        # 탄환이 블랙홀 주변을 지날 때 궤적이 휘어짐
        if hasattr(self, 'game') and hasattr(self.game, 'blackholes') and self.game.blackholes:
            for bh in self.game.blackholes:
                dist_vec = bh.world_pos - self.world_pos
                dist = dist_vec.length()
                if 0 < dist < 250:
                    # 질량에 따른 궤적 휘어짐 (거리가 가까울수록 강함)
                    force = dist_vec.normalize() * (220.0 / (dist + 40.0))
                    self.vel += force
                    if self.vel.length() > 22: self.vel = self.vel.normalize() * 22

        self.world_pos += self.vel
        self.life += 1
        if self.life > 180: self.kill()


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
#  STRUCTURE / FLUID
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


class ShadowSoldier(pygame.sprite.Sprite):
    def __init__(self, owner, pos, etype="basic_drone"):
        super().__init__()
        self.owner = owner
        self.world_pos = Vector2(pos)
        self.life = 1200  # 20초
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        # 그림자 군단 디자인 (보라색 오라 + 검은 핵)
        pygame.draw.circle(self.image, (20, 0, 40, 180), (16, 16), 15)
        pygame.draw.circle(self.image, (100, 0, 255), (16, 16), 11, 2)
        pygame.draw.circle(self.image, (0, 0, 0), (16, 16), 5)
        self.rect = self.image.get_rect()
        self.timer = 0
        self.etype = etype

    def update_screen_pos(self, camera_offset):
        self.rect.center = (int(self.world_pos.x - camera_offset.x),
                            int(self.world_pos.y - camera_offset.y))

    def update(self, enemies, projectiles, dimension, camera_offset):
        self.life -= 1
        if self.life <= 0: 
            self.kill()
            return
        
        # 주인(플레이어) 주변을 호위하며 따라다님
        target = self.owner.world_pos + Vector2(60, 0).rotate(self.life * 1.5)
        move_vec = target - self.world_pos
        if move_vec.length() > 5:
            self.world_pos += move_vec.normalize() * 5
            
        # 자동 공격 로직
        self.timer += 1
        if self.timer % 45 == 0:
            nearest = None
            min_dist = 500
            for e in enemies:
                d = (e.world_pos - self.world_pos).length()
                if d < min_dist:
                    min_dist = d
                    nearest = e
            if nearest:
                fire_dir = (nearest.world_pos - self.world_pos).normalize()
                projectiles.add(Projectile(self.world_pos, fire_dir, dimension, 
                                          color_override=(130, 0, 255), speed=12, dmg=8))


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