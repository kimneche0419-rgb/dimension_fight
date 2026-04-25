import pygame
import random
import math
from entities import (Player, Enemy, Projectile, EnemyProjectile, Gem,
                      Structure, Fluid, RobotCompanion, PickupItem,
                      Particle, Blackhole, ShadowSoldier, Portal, WEAPONS, WEAPON_ORDER,
                      WEAPON_UNLOCK_LEVEL, ENEMY_DATA, ITEM_DATA, SHIP_FORMS,
                      SHIP_COLORS, SETTINGS, JobShrine, JOB_TIER_DATA)
from pygame.math import Vector2


# ─────────────────────────────────────────
#  STAR FIELD
# ─────────────────────────────────────────
class StarField:
    def __init__(self, count=200):
        self.layers = []
        for layer in range(3):
            stars = [(random.uniform(0,3000), random.uniform(0,3000)) for _ in range(count//3)]
            self.layers.append({"stars": stars, "parallax": 0.15+layer*0.25,
                                 "size": layer+1, "bright": 70+layer*55})
        
        #  성운(Nebula) 레이어 추가 (사람이 만든 느낌의 배경 깊이)
        self.nebulae = []
        for _ in range(12):
            self.nebulae.append({
                "pos": (random.uniform(0,3000), random.uniform(0,3000)),
                "size": random.randint(200, 500),
                "color": (random.randint(20,60), random.randint(0,30), random.randint(40,100), 40),
                "parallax": 0.1
            })

    def draw(self, surface, camera_offset, dimension, abyss=False):
        W, H = 800, 600
        # 1. 성운 그리기 (가장 멀리 있음)
        for n in self.nebulae:
            px, py = n["pos"]
            para = n["parallax"]
            x = int((px - camera_offset.x * para) % 3000)
            y = int((py - camera_offset.y * para) % 3000)
            # 메인과 복제본
            for ox in [-3000, 0, 3000]:
                for oy in [-3000, 0, 3000]:
                    fx, fy = x + ox, y + oy
                    if -100 <= fx <= W+100 and -100 <= fy <= H+100:
                        ss = n["size"]
                        try:
                            # 빠른 드로잉 (그라데이션 대신 겹침으로 소프트하게)
                            pygame.draw.circle(surface, n["color"], (fx, fy), ss)
                        except: pass

        for layer in self.layers:
            px = layer["parallax"]
            for sx, sy in layer["stars"]:
                x = int((sx - camera_offset.x * px) % 3000)
                y = int((sy - camera_offset.y * px) % 3000)
                for ox in [-3000,0,3000]:
                    for oy in [-3000,0,3000]:
                        fx = x+ox; fy = y+oy
                        if 0 <= fx <= W and 0 <= fy <= H:
                            b = layer["bright"]
                            if abyss:
                                col = (0, b//2, b)
                            elif dimension == "VOID":
                                col = (b, b//3, b)
                            else:
                                col = (b, b, b+30)
                            pygame.draw.circle(surface, col, (fx,fy), layer["size"])


# ─────────────────────────────────────────
#  CHAPTER
# ─────────────────────────────────────────
class Chapter:
    def __init__(self, name, mode, friction, bg_zones, duration, overview,
                 enemy_set=None, special=None):
        self.name      = name
        self.mode      = mode
        self.friction  = friction
        self.bg_zones  = bg_zones
        self.duration  = duration
        self.overview  = overview
        self.enemy_set = enemy_set or "normal"
        self.special   = special or []

    def get_bg(self, progress, void=False, abyss=False):
        zones = self.bg_zones
        for i in range(len(zones)-1):
            p0,c0 = zones[i]; p1,c1 = zones[i+1]
            if p0 <= progress <= p1:
                t = (progress-p0)/max(p1-p0, 0.0001)
                r = int(c0[0]+(c1[0]-c0[0])*t)
                g = int(c0[1]+(c1[1]-c0[1])*t)
                b = int(c0[2]+(c1[2]-c0[2])*t)
                if void:  r=min(255,r+40); g=min(255,g+20); b=min(255,b+60)
                if abyss: r=max(0,r-20); g=min(255,g+40); b=min(255,b+80)
                return (r,g,b)
        base = zones[-1][1]
        if void:  return tuple(min(255,c+40) for c in base)
        if abyss: return (max(0,base[0]-20), min(255,base[1]+40), min(255,base[2]+80))
        return base


# ─────────────────────────────────────────
#  GAME MANAGER
# ─────────────────────────────────────────
class GameManager:
    SW, SH = 800, 600

    def __init__(self, screen):
        self.screen        = screen
        self.clock         = pygame.time.Clock()
        self.state         = "MENU"
        self.dimension     = "PHYSICAL"
        self.difficulty    = 1.0
        self.camera_offset = Vector2(0,0)

        self.abyss_active   = False
        self.abyss_timer    = 0
        self.ABYSS_DURATION = 3600

        self.blackholes    = pygame.sprite.Group()
        self.bh_spawn_cd   = 0

        self.color_select_active  = False
        self.color_select_idx     = 0
        self.pending_chapter_id   = None

        self.rift_active      = False
        self.rift_boss        = None
        self.rift_enemies     = pygame.sprite.Group()
        self.rift_projectiles = pygame.sprite.Group()
        self.rift_ep          = pygame.sprite.Group()
        self.rift_particles   = []
        self.rift_player_hp_save  = 100
        self.rift_player_pos_save = Vector2(0,0)
        self.rift_timer       = 0

        self.bh_suck_timer   = 0
        self.bh_suck_target  = None
        self.bh_flash_timer  = 0

        self.rift_boss_kill_count = 0

        self.form_select_active = False
        self.form_select_idx    = 0

        self.roulette_active   = False
        self.roulette_timer    = 0
        self.roulette_duration = 180
        self.roulette_idx      = 0
        self.roulette_result   = None
        self.roulette_flash    = 0
        
        self.reward_roulette_active = False
        self.reward_roulette_timer  = 0
        self.reward_roulette_idx    = 0
        self.reward_roulette_result = None
        self.reward_roulette_flash  = 0
        self.last_roulette_time     = 0
        
        self.respec_dialog_open = False

        self.settings_open     = False
        self.settings_sel      = 0

        self.respec_confirm_active = False
        self.respec_in_progress    = False

        # 상점 탭 (0=업그레이드/스킬, 1=직업마켓)
        self.shop_tab = 0
        self.job_market_sel = 0
        self.owned_jobs = ["전사"]  # 보유 중인 직업 리스트

        #  심해 잠수 전용 상태
        self.dive_spawn_timer = 0

        #  연속킬 streak 이펙트 타이머
        self.streak_flash_timer = 0
        self.streak_flash_count = 0

        self.chapters = {
            "0": Chapter(
                "전직의 시련", "SHIP", -0.05,
                [(0.0,(40,10,20)),(0.5,(120,10,40)),(1.0,(180,20,50))],
                90, "심판의 전장 · 90초 생존 · 전직 자격 심사 · 재전직 가능",
                enemy_set="abyss", special=["abyss_enemies", "mega_bosses"]
            ),
            "1": Chapter(
                "섹터 제로: 궤도의 정적", "SHIP", -0.02,
                [(0.0,(10,20,30)),(0.4,(5,30,60)),(0.7,(30,10,50)),(1.0,(60,5,20))],
                3600, "무중력 전투 · 기초 훈련 · 스페이스 대쉬 · 시간 무제한",
                enemy_set="normal",
            ),
            "2": Chapter(
                "제9구역: 네온 유적", "HUMAN", -0.25,
                [(0.0,(30,30,40)),(0.3,(40,25,35)),(0.6,(20,20,50)),(1.0,(50,10,10))],
                3600, "폐허가 된 거대도시 · 보병 작전 · 높은 구조물 밀도",
                enemy_set="normal",
            ),
            "3": Chapter(
                "반타블랙 심해", "SHIP", -0.18,
                [(0.0,(5,30,40)),(0.3,(0,50,60)),(0.6,(0,30,80)),(1.0,(0,10,60))],
                3600, "심해 비행 · [Z] 잠수 · 수압 위험 · 네온 서펜트",
                enemy_set="abyss", special=["toxic_fluid","abyss_enemies","deep_gravity","diving"],
            ),
            "4": Chapter(
                "이벤트 호라이즌", "SHIP", -0.05,
                [(0.0,(20,0,40)),(0.3,(40,0,60)),(0.6,(60,0,80)),(1.0,(80,0,100))],
                3600, "공허의 균열 · 차원 대적자 · 빈번한 블랙홀 발생",
                enemy_set="void", special=["frequent_blackhole","void_enemies"],
            ),
            "5": Chapter(
                "싱귤래리티 코어", "SHIP", -0.05,
                [(0.0,(40,10,20)),(0.3,(60,5,5)),(0.6,(10,10,60)),(1.0,(5,40,50))],
                3600, "중력 우물 · 극한의 난이도 · 모든 적 출현",
                enemy_set="all",
            ),
            "6": Chapter(
                "최종 수렴점", "SHIP", -0.03,
                [(0.0,(0,10,30)),(0.3,(0,5,50)),(0.7,(20,0,60)),(1.0,(40,0,80))],
                3600, "승천한 심연 · 군주의 존재 · 블랙홀 지옥",
                enemy_set="all", special=["frequent_blackhole","void_enemies","abyss_enemies","mega_bosses","diving"],
            ),
            "7": Chapter(
                "직업 각성의 성소", "SHIP", -0.05,
                [(0.0,(30,50,100)),(0.5,(50,100,180)),(1.0,(80,150,255))],
                60, "전직의 기회 · 60초 생존 시 즉시 전직",
                enemy_set="normal", special=["job_awakening"]
            ),
            "8": Chapter(
                "승급의 투기장", "HUMAN", -0.15,
                [(0.0,(100,20,20)),(0.5,(150,50,20)),(1.0,(255,100,0))],
                120, "극한 전투 · 120초 생존 시 직업 티어 상승",
                enemy_set="all", special=["tier_promotion", "frequent_blackhole"]
            )
        }


        self.current_chapter = None

        self.enemies           = pygame.sprite.Group()
        self.projectiles       = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.gems              = pygame.sprite.Group()
        self.structures        = pygame.sprite.Group()
        self.fluids            = pygame.sprite.Group()
        self.companions        = pygame.sprite.Group()
        self.allies            = pygame.sprite.Group()
        self.items             = pygame.sprite.Group()
        self.player            = None
        self.freeze_timer      = 0
        self.shop_scroll_y     = 0

        self.game_time   = 0
        self.spawn_timer = 0
        self.mouse_pos   = (400,300)
        self.notify_text  = ""
        self.notify_timer = 0
        self.levelup_choices = []
        self.levelup_active  = False

        # 전직 시스템
        self.job_select_active  = False
        self.job_select_choices = []   # 제시할 직업 key 목록 (3개)
        self.job_select_timer   = 0    # 전직 창 애니메이션 타이머
        self.particles = []
        self.star_field = StarField(180)
        self.high_score = 0
        self.shake_timer  = 0
        self.shake_amount = 0
        self.item_timer   = 0

        from entities import PERSISTENT_UPGRADES
        self.gold     = 0
        self.diamonds = 0
        self.crystals = 0  # Legacy or for special use
        self.upgrades = {k: 0 for k in PERSISTENT_UPGRADES}
        self.owned_skills = {}  # {skill_name: level}
        self.equipped_skills = []  # 장착된 스킬 키 리스트 (최대 6개)
        self.shop_sel = 0
        self.skill_manage_open = False  # 스킬 관리 UI 열림 여부
        self.skill_manage_sel = 0

        #  리워드 룰렛 관련
        self.reward_roulette_active = False
        self.reward_roulette_timer  = 0
        self.reward_roulette_idx    = 0
        self.reward_roulette_result = None
        self.reward_roulette_flash  = 0
        self.last_roulette_time     = 0   #  룰렛 쿨타임용 (Unix Timestamp)
        
        #  멀티버스(Multiverse) 시스템
        self.universe_type = "PRIME"
        self.universe_timer = 0
        self.universe_cycle = 7200 # 2분마다 전환 (120초 * 60프레임)
        self.universes = {
            "PRIME": {"name": "프라임 현실", "color": (100, 150, 255), "buff": "표준 차원", "effect": None},
            "CYBER": {"name": "사이버 넷", "color": (255, 255, 0), "buff": "이동속도 +20% / 적 탄속 +20%", "effect": "cyber_glow"},
            "ABYSSAL": {"name": "심연의 틈", "color": (150, 0, 255), "buff": "공격력 +50% / 시야 제한", "effect": "darkness"},
            "GOLDEN": {"name": "황금의 도래", "color": (255, 200, 50), "buff": "보상 2배 / 최대 체력 절반", "effect": "gold_filter"},
            "GLITCH": {"name": "글리치 월드", "color": (255, 50, 50), "buff": "무작위 대쉬 / 모든 사격 관통", "effect": "jitter"}
        }
        
        #  사용자 프로필 (설정에서 변경 가능)
        self.pilot_name = "KIM"
        self.pilot_rank = "COMMANDER"
        self.pilot_callsign = "RAVEN-01"

        self._weapon_inv_slots = []  # [(rect, wkey), ...] 클릭 감지용
        self._load_data()
        
        # ★ 실존 우주 이론: 엔트로피 & 열적 죽음 (Heat Death)
        self.entropy       = 0.0
        self.entropy_max   = 1.0
        self.entropy_rate  = 0.00002 # 매우 느리게 증가
        
        # ★ 멀티버스 포탈 시스템
        self.portals            = pygame.sprite.Group()
        self.portal_suck_timer  = 0
        self.portal_suck_target = None
        
        # 엘리트 서지 웨이브 시스템
        self.surge_timer   = 0
        self.surge_warning = 0   # 경고 표시 프레임

        #  프리미엄 UI 효과용 서피스
        self.scanline_surf = pygame.Surface((800, 600), pygame.SRCALPHA)
        for y in range(0, 600, 3):
            pygame.draw.line(self.scanline_surf, (0, 0, 0, 45), (0, y), (800, y))

        #  직업 뷰어(Job Viewer) 상태
        self.job_viewer_active = False
        self.job_categories = {
            "STRIKER":  ["전사", "탱커", "학살자"],
            "SPECIALIST": ["저격수", "기계공", "마법사"],
            "VANGUARD":   ["파일럿", "광속"],
            "ANOMALY":    ["차원술사", "흡혈귀"]
        }
        self.job_cat_names = {
            "STRIKER": "전투형 (STRIKER)",
            "SPECIALIST": "기술형 (SPECIALIST)",
            "VANGUARD": "기동형 (VANGUARD)",
            "ANOMALY": "특수형 (ANOMALY)"
        }



    # ─────────────────────────────────────
    def start_game(self, chapter_id):
        self.pending_chapter_id  = chapter_id
        self.color_select_active = True
        self.color_select_idx    = 0
        self.state = "COLOR_SELECT"

    def _do_start_game(self, chapter_id):
        ch = self.chapters[chapter_id]
        self.current_chapter = ch
        self.player = Player((0,0))
        self.player.active_skills = list(self.equipped_skills) #  장착된 스킬만 부여
        self.player.mode = ch.mode
        self.player.set_dimension("PHYSICAL")
        self.player.ship_color_key = SHIP_COLORS[self.color_select_idx]["key"]
        self.dimension = "PHYSICAL"
        self.camera_offset = Vector2(-400,-300)
        self.abyss_active = False
        self.abyss_timer  = 0
        self.blackholes.empty()
        self.bh_spawn_cd  = 0
        self.bh_suck_timer  = 0
        self.bh_suck_target = None
        self.bh_flash_timer = 0
        self.rift_active    = False
        self.rift_boss      = None
        self.rift_enemies.empty()
        self.rift_projectiles.empty()
        self.rift_ep.empty()
        self.rift_particles.clear()
        self.form_select_active = False
        self.rift_boss_kill_count = 0
        self.dive_spawn_timer = 0
        self.streak_flash_timer = 0

        for g in [self.enemies, self.projectiles, self.enemy_projectiles,
                  self.gems, self.structures, self.fluids, self.companions, self.allies, self.items]:
            g.empty()
        self.particles.clear()
        self.freeze_timer = 0

        if "abyss" in ch.enemy_set or "3" == chapter_id:
            if "abyss_ship" not in self.player.unlocked_forms:
                self.player.unlocked_forms.append("abyss_ship")
            self.player.morph_to("abyss_ship")

        if ch.mode == "HUMAN":
            for _ in range(25):
                wx = random.randint(-2500,2500); wy = random.randint(-2500,2500)
                self.structures.add(Structure((wx,wy,random.randint(60,200),random.randint(60,200))))
        if "toxic_fluid" in ch.special:
            for _ in range(12):
                fx = random.randint(-2000,2000); fy = random.randint(-2000,2000)
                self.fluids.add(Fluid((fx,fy,280,160),(0,120,80,110)))

        self.game_time      = 0
        self.spawn_timer    = 0
        self.difficulty     = 1.0
        self.state          = "PLAYING"
        self.levelup_active = False
        self.item_timer     = 0

        if "diving" in ch.special:
            self.notify("WASD이동  SPACE대쉬  SHIFT차원전환  F변형  [Z]심해잠수!", 260)
        else:
            self.notify("WASD 이동  SPACE 대쉬  SHIFT 차원전환  F 변형", 220)

        #  영구 업그레이드 적용
        for k in self.upgrades:
            self._apply_permanent_boost(k)
        u = self.upgrades
        self.player.max_health += u.get("hp_boost", 0) * 10
        self.player.health = self.player.max_health
        self.player.max_shield += u.get("shield_boost", 0) * 5
        self.player.shield = self.player.max_shield
        # 속도, CDR 등은 Player.get_speed_mult 등에서 적용되도록 entities.py 수정 필요 또는 여기서 직접 속성 부여
        self.player._speed_upg_mult = 1.0 + u.get("speed_boost", 0) * 0.03
        self.player._xp_upg_mult    = 1.0 + u.get("xp_bonus", 0) * 0.05
        self.player._dash_cdr_mult  = 1.0 - u.get("dash_cdr", 0) * 0.05


    # ─────────────────────────────────────
    def notify(self, text, duration=120):
        self.notify_text  = text
        self.notify_timer = duration

    def screen_shake(self, amount=8, frames=10):
        self.shake_amount = amount
        self.shake_timer  = frames

    def _update_camera(self):
        target = self.player.world_pos - Vector2(self.SW//2, self.SH//2)
        self.camera_offset += (target - self.camera_offset) * SETTINGS.camera_smooth

    _MAX_PARTICLES = 400

    def _burst(self, world_pos, color, count=12, speed=4, life=30):
        slots = self._MAX_PARTICLES - len(self.particles)
        if slots <= 0:
            return
        count = min(count, slots)
        for _ in range(count):
            a   = random.uniform(0, 360)
            spd = random.uniform(1, speed)
            vel = Vector2(math.cos(math.radians(a))*spd, math.sin(math.radians(a))*spd)
            self.particles.append(Particle(world_pos, vel, color,
                                           life+random.randint(-5,5), random.randint(2,5)))

    # ─────────────────────────────────────
    #  BLACKHOLE SPAWN
    # ─────────────────────────────────────
    def _try_spawn_blackhole(self):
        ch = self.current_chapter
        base_prob = 0.003
        if "frequent_blackhole" in ch.special:
            base_prob = 0.010
        if self.bh_spawn_cd > 0:
            self.bh_spawn_cd -= 1
            return
        if random.random() < base_prob and len(self.blackholes) < 3:
            angle = random.uniform(0,360)
            dist  = random.uniform(200, 500)
            pos   = self.player.world_pos + Vector2(
                math.cos(math.radians(angle))*dist,
                math.sin(math.radians(angle))*dist)
            bh = Blackhole(pos)
            self.blackholes.add(bh)
            self.bh_spawn_cd = 600
            self.notify(" 블랙홀 발생!", 120)
            self.screen_shake(8, 10)
            self._burst(pos, (180,0,255), count=30, speed=8, life=50)

    def _update_blackholes(self):
        if self.bh_suck_timer > 0:
            self.bh_suck_timer -= 1
            if self.bh_suck_timer == 30:
                self.bh_flash_timer = 25
            if self.bh_suck_timer == 0:
                self._enter_rift()
            return

        for bh in self.blackholes:
            bh.update()
            pull = bh.apply_pull(self.player.world_pos, self.player.vel)
            self.player.vel += pull
            for enemy in self.enemies:
                p = bh.apply_pull(enemy.world_pos, enemy.vel)
                enemy.world_pos += p * 2
            for enemy in list(self.enemies):
                d = (bh.world_pos - enemy.world_pos).length()
                if d < bh.radius:
                    self._burst(enemy.world_pos, (180,0,255), count=8)
                    self.gems.add(Gem(enemy.world_pos, enemy.gem_val))
                    enemy.kill()
            for ep in list(self.enemy_projectiles):
                d = (bh.world_pos - ep.world_pos).length()
                if d < bh.radius + 20:
                    ep.kill()

            player_d = (bh.world_pos - self.player.world_pos).length()
            
            # ★ 실존 우주 이론: 호킹 복사 (Hawking Radiation)
            # 블랙홀 근처에 있으면 에너지를 흡수하여 스킬 쿨타임이 빨리 돌지만, 방사능으로 체력이 소모됨
            if player_d < 250:
                # 체력 소모 (방사능 노출)
                self.player.health -= 0.04
                # 스킬 쿨타임 가속 (에너지 흡수)
                for skey in self.player.skill_cooldowns:
                    if self.player.skill_cooldowns[skey] > 0:
                        self.player.skill_cooldowns[skey] -= 1
                if self.game_time % 20 == 0:
                    self._burst(self.player.world_pos, (180, 0, 255, 100), count=3, speed=2)

            if player_d < bh.radius * 0.6 and not self.rift_active and self.bh_suck_timer == 0:
                self.bh_suck_timer  = 60
                self.bh_suck_target = bh
                self.rift_player_hp_save  = self.player.health
                self.rift_player_pos_save = Vector2(self.player.world_pos)
                self.screen_shake(20, 30)
                self._burst(self.player.world_pos, (200,0,255), count=40, speed=10, life=60)
                self.notify(" 블랙홀에 흡입됨! 제3차원으로...", 100)
                return

            if not bh.alive:
                bh.kill()
                self._activate_abyss(bh.world_pos)

        if self.abyss_active:
            self.abyss_timer -= 1
            self.player.abyss_mode = True
            if self.abyss_timer <= 0:
                self.abyss_active = False
                self.player.abyss_mode = False
                self.notify("심해 차원 종료...", 120)
        else:
            self.player.abyss_mode = False

    def _activate_abyss(self, center_pos):
        self.abyss_active = True
        self.abyss_timer  = self.ABYSS_DURATION
        self.notify(" 심해 차원 개방! 60초", 200)
        self.screen_shake(15, 20)
        self._burst(center_pos, (0,200,255), count=50, speed=10, life=80)
        for _ in range(8):
            angle = random.uniform(0,360)
            dist  = random.uniform(200,450)
            sp    = center_pos + Vector2(math.cos(math.radians(angle))*dist,
                                          math.sin(math.radians(angle))*dist)
            etype = random.choice(["abyss_eel","depth_guardian","leviathan_eye"])
            self.enemies.add(Enemy(sp, "PHYSICAL", etype, self.difficulty+1))
        self._drop_item_at(center_pos, "shield")
        self._drop_item_at(center_pos + Vector2(50,0), "hp")

    # ─────────────────────────────────────
    #  RIFT DIMENSION
    # ─────────────────────────────────────
    def _enter_rift(self):
        self.rift_active = True
        self.rift_timer  = 0
        self.rift_enemies.empty()
        self.rift_projectiles.empty()
        self.rift_ep.empty()
        self.rift_particles.clear()

        RIFT_BOSS_POOL = [
            "rift_guardian","rift_devourer","void_wraith_king",
            "rift_colossus","entropy_core","abyss_rift_lord",
        ]
        k = self.rift_boss_kill_count
        boss_idx  = k % len(RIFT_BOSS_POOL)
        boss_type = RIFT_BOSS_POOL[boss_idx]
        scale_mult = 1.0 + k * 0.35

        boss_pos = Vector2(0, -200)
        boss_diff = self.difficulty + 1 + k * 0.5
        self.rift_boss = Enemy(boss_pos, "PHYSICAL", boss_type, boss_diff)
        self.rift_boss.hp     = int(self.rift_boss.max_hp * scale_mult)
        self.rift_boss.max_hp = self.rift_boss.hp
        self.rift_boss.speed  = min(self.rift_boss.speed * (1 + k * 0.15), self.rift_boss.speed * 3)
        self.rift_enemies.add(self.rift_boss)

        minion_count = min(4 + k, 8)
        minion_pool  = ["null_fragment","void_titan","echo_phantom",
                        "glitcher","shadow_lurker","abyss_eel"]
        for i in range(minion_count):
            a  = i * (360 // minion_count)
            sp = Vector2(math.cos(math.radians(a))*250, math.sin(math.radians(a))*250)
            mtype = random.choice(minion_pool)
            self.rift_enemies.add(Enemy(sp, "PHYSICAL", mtype, self.difficulty + k * 0.3))

        self.player.world_pos = Vector2(0, 0)
        self.player.vel       = Vector2(0, 0)
        self.camera_offset    = Vector2(-400, -300)
        self.bh_flash_timer   = 40

        boss_name = ENEMY_DATA[boss_type]["name"]
        if k == 0:
            msg = f" 제3차원 돌입! {boss_name}를 처치하라!"
        else:
            msg = f" 제3차원! 강화된 {boss_name} (×{scale_mult:.1f})!"
        self.notify(msg, 240)
        self.screen_shake(18, 25)

    def _update_rift(self, keys, events):
        self.rift_timer += 1

        friction = -0.18
        self.player.update(keys, friction, self.current_chapter.mode, self.mouse_pos)
        self._update_camera()

        self.player.timer += 1
        if self.player.timer > self.player.weapon_cooldown:
            self.player.timer = 0
            self._rift_auto_shoot()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._rift_manual_shoot(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: self._use_skill(0)
                elif event.key == pygame.K_2: self._use_skill(1)
                elif event.key == pygame.K_3: self._use_skill(2)
                elif event.key == pygame.K_4: self._use_skill(3)
                elif event.key == pygame.K_5: self._use_skill(4)
                elif event.key == pygame.K_6: self._use_skill(5)


        # 스텔스 체크: 클로킹 중이면 적이 플레이어를 추적하지 않음
        effective_p_pos = self.player.world_pos
        if self.player.skill_stealth_timer > 0:
            effective_p_pos = self.player.world_pos + Vector2(10000, 10000)

        rift_list = list(self.rift_enemies)
        for enemy in rift_list:
            if self.freeze_timer > 0 and enemy.special != "phase_boss":
                continue
            enemy.update(effective_p_pos,
                         enemy_projectiles=self.rift_ep,
                         dimension="PHYSICAL",
                         all_enemies=rift_list)

        for ally in self.allies:
            ally.update(self.rift_enemies, self.rift_projectiles, "PHYSICAL", self.camera_offset)

        for p in list(self.rift_projectiles):
            p.update()
            p_r = pygame.Rect(p.world_pos.x-6, p.world_pos.y-6, 12,12)
            for enemy in list(self.rift_enemies):
                er = pygame.Rect(enemy.world_pos.x-enemy.rect.w//2,
                                 enemy.world_pos.y-enemy.rect.h//2,
                                 enemy.rect.w, enemy.rect.h)
                if er.colliderect(p_r):
                    #  약점 시스템 타격 판정
                    is_crit = False
                    if enemy.weak_point and enemy.weak_point.check_hit(p.world_pos, enemy.world_pos):
                        is_crit = True
                    
                    dmg = int(p.dmg * self.player.get_dmg_mult())
                    if is_crit: 
                        dmg *= 3
                        self.notify(" CRITICAL HIT!!", 40)
                    
                    if enemy.take_damage(dmg):
                        #  리프트 내 뱀파이어리즘 흡혈
                        if self.player.skill_vamp_timer > 0:
                            v_lvl = self.owned_skills.get("vampirism", 1)
                            if random.random() < (0.3 + v_lvl * 0.1):
                                self.player.health = min(self.player.max_health, self.player.health + 1 + v_lvl)
                                self._rift_burst(enemy.world_pos, (255, 0, 0), count=15)
                        
                        #  리프트 내 뇌창 폭발
                        if getattr(p, "special", None) == "thunder_spear":
                            self._burst(p.world_pos, (255,100,0), count=30, speed=8)
                            for e_near in list(self.rift_enemies):
                                if (e_near.world_pos - p.world_pos).length() < 120:
                                    e_near.take_damage(p.dmg)

                        self._rift_burst(enemy.world_pos, (200,50,255), count=18)
                        if enemy is self.rift_boss:
                            self.rift_boss = None
                        enemy.kill()
                        r_pts = 500
                        if getattr(self, "universe_type", "PRIME") == "GOLDEN": r_pts *= 2
                        self.player.score += r_pts
                    if enemy.special != "phase_boss":
                        p.kill()
                    break

        player_wr = pygame.Rect(self.player.world_pos.x-14, self.player.world_pos.y-14, 28,28)
        if self.player.skill_titan_timer > 0:
            player_wr = pygame.Rect(self.player.world_pos.x-30, self.player.world_pos.y-30, 60,60)

        for ep in list(self.rift_ep):
            ep.update()
            ep_r = pygame.Rect(ep.world_pos.x-7, ep.world_pos.y-7, 14,14)
            if ep_r.colliderect(player_wr) and self.player.invincible <= 0:
                actual = self.player.take_hit(ep.dmg)
                self.screen_shake(5,6)
                ep.kill()
                if self.player.health <= 0:
                    self._grant_death_rewards()
                    return

        if self.player.invincible <= 0:
            for enemy in list(self.rift_enemies):
                er = pygame.Rect(enemy.world_pos.x-enemy.rect.w//2,
                                 enemy.world_pos.y-enemy.rect.h//2,
                                 enemy.rect.w, enemy.rect.h)
                if er.colliderect(player_wr):
                    actual = self.player.take_hit(15)
                    self.screen_shake(6,8)
        if self.player.invincible > 0:
            self.player.invincible -= 1

        self.rift_particles = [p for p in self.rift_particles if p.update()]

        if self.rift_boss is None or not self.rift_boss.alive():
            self._exit_rift()

    def _rift_auto_shoot(self):
        w   = self.player.weapon
        col = w["color_p"]
        fire_dir = self.player.get_fire_direction(self.mouse_pos)
        for _ in range(w["count"]):
            sa  = random.uniform(-w["spread"]/2, w["spread"]/2)
            rad = math.radians(sa)
            rotated = Vector2(fire_dir.x*math.cos(rad)-fire_dir.y*math.sin(rad),
                              fire_dir.x*math.sin(rad)+fire_dir.y*math.cos(rad))
            self.rift_projectiles.add(Projectile(self.player.world_pos, rotated, "PHYSICAL",
                                                 color_override=(200,80,255), speed=w["speed"],
                                                 dmg=w["dmg"], is_direction=True, size=w["size"]))

    def _rift_manual_shoot(self, screen_pos):
        w   = self.player.weapon
        fire_dir = self.player.get_fire_direction(screen_pos)
        for _ in range(w["count"]):
            sa  = random.uniform(-w["spread"]/2, w["spread"]/2)
            rad = math.radians(sa)
            rotated = Vector2(fire_dir.x*math.cos(rad)-fire_dir.y*math.sin(rad),
                              fire_dir.x*math.sin(rad)+fire_dir.y*math.cos(rad))
            self.rift_projectiles.add(Projectile(self.player.world_pos, rotated, "PHYSICAL",
                                                 color_override=(200,80,255), speed=w["speed"],
                                                 dmg=w["dmg"], is_direction=True, size=w["size"]))
        self.player.timer = 0

    def _rift_burst(self, world_pos, color, count=12, speed=4, life=30):
        slots = self._MAX_PARTICLES - len(self.rift_particles)
        if slots <= 0:
            return
        count = min(count, slots)
        for _ in range(count):
            a   = random.uniform(0, 360)
            spd = random.uniform(1, speed)
            vel = Vector2(math.cos(math.radians(a))*spd, math.sin(math.radians(a))*spd)
            self.rift_particles.append(Particle(world_pos, vel, color,
                                                life+random.randint(-5,5), random.randint(2,5)))

    def _exit_rift(self):
        self.rift_active = False
        self.player.world_pos = Vector2(self.rift_player_pos_save)
        self.player.vel       = Vector2(0,0)
        self.camera_offset    = self.player.world_pos - Vector2(400, 300)
        if self.bh_suck_target in self.blackholes:
            self.bh_suck_target.kill()
        self.bh_suck_target = None

        self.rift_boss_kill_count += 1
        k = self.rift_boss_kill_count
        bonus_score = 500 + (k - 1) * 300
        self.player.score += bonus_score
        hp_bonus = max(20, 50 - (k - 1) * 5)
        self.player.health = min(self.player.max_health, self.player.health + hp_bonus)
        extra = ""
        if k % 3 == 0:
            self.player._cd_bonus += 1
            extra = "  사격속도 +1!"

        self.bh_flash_timer = 35
        self.screen_shake(15, 20)
        self._burst(self.player.world_pos, (100,255,200), count=50, speed=9, life=70)
        self.notify(
            f" 제3차원 탈출! HP+{hp_bonus}  SCORE+{bonus_score}"
            f"  [보스처치:{k}회]{extra}", 280)

    # ─────────────────────────────────────
    def _on_dimension_shift(self):
        prob = 0.30 if "frequent_blackhole" in self.current_chapter.special else 0.15
        if random.random() < prob:
            self._force_spawn_blackhole()
        # ★ 차원 전환 시 비-보스 적 교체 (일부)
        self._replace_enemies_on_shift()

    def _force_spawn_blackhole(self):
        if len(self.blackholes) >= 4: return
        angle = random.uniform(0,360)
        dist  = random.uniform(150, 350)
        pos   = self.player.world_pos + Vector2(
            math.cos(math.radians(angle))*dist,
            math.sin(math.radians(angle))*dist)
        bh = Blackhole(pos)
        self.blackholes.add(bh)
        self.notify(" 차원 충격! 블랙홀 발생!", 130)
        self.screen_shake(10, 12)
        self._burst(pos, (200,50,255), count=20, speed=7, life=45)

    # ─────────────────────────────────────
    #  ENEMY REPLACEMENT ON SHIFT
    # ─────────────────────────────────────
    def _replace_enemies_on_shift(self):
        """차원 전환 시 비-보스 적 일부를 교체"""
        boss_types = {"nexus_overmind","abyssal_tyrant","void_god","abyss_sovereign",
                      "echo_wraith","dreadnought_construct","anomaly_core",
                      "abyss_leviathan","abyss_hydra","null_colossus",
                      "rift_guardian","rift_devourer","void_wraith_king",
                      "rift_colossus","entropy_core","abyss_rift_lord"}
        
        replaceable = [e for e in self.enemies if e.etype not in boss_types]
        replace_count = max(1, len(replaceable) * 4 // 10)  # 40% 교체
        
        ch = self.current_chapter
        abyss_pool = ["abyss_eel","depth_guardian","leviathan_eye","deep_angler"]
        void_pool  = ["null_fragment","void_titan","echo_phantom","glitcher"]
        normal_pool = ["basic_drone","swarm_organism","glitcher","hunter_drone",
                       "sentinel","sniper_node","elite_enforcer","void_weaver",
                       "corrupted_sentry","shadow_lurker"]
        
        if self.dimension == "VOID":
            pool = void_pool
        elif ch.enemy_set == "abyss":
            pool = abyss_pool
        elif ch.enemy_set == "all":
            pool = normal_pool + void_pool
        else:
            pool = normal_pool
        
        targets = random.sample(replaceable, min(replace_count, len(replaceable)))
        for enemy in targets:
            pos = Vector2(enemy.world_pos)
            dim = self.dimension
            etype = random.choice(pool)
            self._burst(enemy.world_pos, (200,100,255), count=8, speed=4)
            enemy.kill()
            self.enemies.add(Enemy(pos, dim, etype, self.difficulty))
    
    def _enchant_enemies_on_universe_shift(self):
        """멀티버스 전환 시 기존 적에 인챈트 부여 + 전용 엘리트 소환"""
        from entities import ENEMY_DATA
        boss_types = {"nexus_overmind","abyssal_tyrant","void_god","abyss_sovereign",
                      "echo_wraith","dreadnought_construct","anomaly_core",
                      "abyss_leviathan","abyss_hydra","null_colossus"}

        # 유니버스별 인챈트 타입
        enchant_map = {
            "PRIME":   None,
            "CYBER":   "overcharged",
            "ABYSSAL": "shadowed",
            "GOLDEN":  "gilded",
            "GLITCH":  "glitched",
        }
        # 유니버스별 전용 엘리트 적
        unique_map = {
            "CYBER":   "cyber_enforcer",
            "ABYSSAL": "abyss_specter",
            "GOLDEN":  "golden_golem",
            "GLITCH":  "glitch_ghost",
        }

        enchant = enchant_map.get(self.universe_type)
        u_color = self.universes[self.universe_type]["color"]

        # 기존 비-보스 적에게 인챈트 적용
        for enemy in list(self.enemies):
            if enemy.etype not in boss_types:
                enemy.multiverse_type = self.universe_type
                if hasattr(enemy, "apply_enchant"):
                    enemy.apply_enchant(enchant)
                self._burst(enemy.world_pos, u_color, count=4, speed=4, life=25)

        # 유니버스 전용 엘리트 1~2마리 소환
        unique = unique_map.get(self.universe_type)
        if unique and unique in ENEMY_DATA:
            count = 2 if len(list(self.enemies)) < 8 else 1
            for _ in range(count):
                angle = random.uniform(0, 360)
                dist  = random.uniform(260, 420)
                pos   = self.player.world_pos + Vector2(
                    math.cos(math.radians(angle)) * dist,
                    math.sin(math.radians(angle)) * dist)
                e = Enemy(pos, "PHYSICAL", unique, self.difficulty + 1.0)
                e.multiverse_type = self.universe_type
                if hasattr(e, "apply_enchant") and enchant:
                    e.apply_enchant(enchant)
                self.enemies.add(e)
                self._burst(pos, u_color, count=12, speed=6, life=35)

    # ─────────────────────────────────────
    #  UPDATE
    # ─────────────────────────────────────
    def update(self, events):
        self.mouse_pos = pygame.mouse.get_pos()
        if self.freeze_timer > 0: self.freeze_timer -= 1
        if hasattr(self, "skill_combo_timer") and self.skill_combo_timer > 0:
            self.skill_combo_timer -= 1
        else:
            if hasattr(self, "skill_combo_list"): self.skill_combo_list = []
            
        #  고무고무 가틀링 주먹 효과
        if self.player and self.player.skill_gatling_timer > 0:
            lvl = self.owned_skills.get("gomu_gatling", 1)
            if self.player.skill_gatling_timer % 3 == 0:
                for _ in range(2 + lvl // 2):
                    angle = random.uniform(0,360)
                    dist = random.uniform(50, 150 + lvl * 10)
                    p_pos = self.player.world_pos + Vector2(math.cos(math.radians(angle))*dist, math.sin(math.radians(angle))*dist)
                    self._burst(p_pos, (255, 180, 100), count=10 + lvl, speed=5 + lvl//2)
                    target_enemies = self.rift_enemies if self.rift_active else self.enemies
                    for e in list(target_enemies):
                        if (e.world_pos - p_pos).length() < 70 + lvl * 5:
                            e.take_damage(20 + lvl * 10)
        if self.notify_timer > 0: self.notify_timer -= 1
        
        #  직업 뷰어(Job Viewer) 입력 처리
        if self.job_viewer_active:
            self._handle_job_viewer_input(events)
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_j:
                    self.job_viewer_active = True
                    return
        if self.shake_timer   > 0: self.shake_timer   -= 1
        if self.bh_flash_timer > 0: self.bh_flash_timer -= 1
        if self.roulette_flash > 0: self.roulette_flash -= 1
        if self.streak_flash_timer > 0: self.streak_flash_timer -= 1
        
        #  글로벌 사망/부활 체크 (모든 상태에서 공통 적용)
        if self.player and self.player.health <= 0 and self.state not in ["MENU", "SHOP", "DEATH"]:
            self._grant_death_rewards()
            if self.state == "DEATH": return

        if self.settings_open:
            for event in events:
                self._handle_settings_input(event)
            return

        # 챕터 룰렛 시스템 제거됨


        #  리워드 룰렛 업데이트
        if self.reward_roulette_active:
            self.reward_roulette_timer += 1
            dur = 120
            t = self.reward_roulette_timer / dur
            speed = max(1, int(10 - t * 9))
            if self.reward_roulette_timer % speed == 0:
                self.reward_roulette_idx = (self.reward_roulette_idx + 1) % 8
            if self.reward_roulette_timer >= dur:
                self.reward_roulette_active = False
                self._apply_reward_roulette_result()
                self.reward_roulette_flash = 120
            return

        if self.state == "COLOR_SELECT":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.color_select_idx = (self.color_select_idx - 1) % len(SHIP_COLORS)
                    elif event.key == pygame.K_RIGHT:
                        self.color_select_idx = (self.color_select_idx + 1) % len(SHIP_COLORS)
                    elif event.key == pygame.K_UP:
                        self.color_select_idx = (self.color_select_idx - 4) % len(SHIP_COLORS)
                    elif event.key == pygame.K_DOWN:
                        self.color_select_idx = (self.color_select_idx + 4) % len(SHIP_COLORS)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._do_start_game(self.pending_chapter_id)
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                        self.color_select_active = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for i in range(len(SHIP_COLORS)):
                        row = i // 4; ci = i % 4
                        bx = 80 + ci * 165; by = 240 + row * 140
                        card = pygame.Rect(bx, by, 150, 120)
                        if card.collidepoint(mx, my):
                            self.color_select_idx = i
                            self._do_start_game(self.pending_chapter_id)
                            break
                            break
            return

        if self.state == "SHOP":
            for event in events:
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL, pygame.MOUSEMOTION):
                    self._handle_shop_mouse(event)
                else:
                    self._handle_shop_input(event)
            return

        if self.rift_active:

            keys = pygame.key.get_pressed()
            self._update_rift(keys, events)
            return

        if self.form_select_active:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    forms = self.player.unlocked_forms
                    if event.key == pygame.K_LEFT:
                        self.form_select_idx = (self.form_select_idx-1) % len(forms)
                    elif event.key == pygame.K_RIGHT:
                        self.form_select_idx = (self.form_select_idx+1) % len(forms)
                    elif event.key in (pygame.K_RETURN, pygame.K_f):
                        chosen = forms[self.form_select_idx]
                        self.player.morph_to(chosen)
                        self.form_select_active = False
                        self.notify(f"변형: {SHIP_FORMS[chosen]['name']}", 120)
                        self._burst(self.player.world_pos, (255,200,50), count=20)
                    elif event.key == pygame.K_ESCAPE:
                        self.form_select_active = False
            return

        if self.job_select_active:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1 and len(self.job_select_choices) >= 1: self._apply_job(0)
                    elif event.key == pygame.K_2 and len(self.job_select_choices) >= 2: self._apply_job(1)
                    elif event.key == pygame.K_3 and len(self.job_select_choices) >= 3: self._apply_job(2)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 카드 클릭 감지 (Phase 2: 타이머 >= 100)
                    if self.job_select_timer >= 100:
                        mx, my = event.pos
                        card_w, card_h = 220, 248
                        total_w = card_w * 3 + 24
                        start_x = (800 - total_w) // 2
                        for i in range(len(self.job_select_choices)):
                            cx = start_x + i * (card_w + 12)
                            cy = 140
                            if cx <= mx <= cx + card_w and cy <= my <= cy + card_h:
                                self._apply_job(i)
                                break
            return

        if self.levelup_active:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1 and len(self.levelup_choices)>=1: self._apply_levelup_choice(0)
                    elif event.key == pygame.K_2 and len(self.levelup_choices)>=2: self._apply_levelup_choice(1)
                    elif event.key == pygame.K_3 and len(self.levelup_choices)>=3: self._apply_levelup_choice(2)
            return

        if self.state == "MENU":
            self.game_time += 1
            self._handle_menu_input(events)
            return

        if self.state == "DEATH":
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.state = "MENU"
            return
            
        if self.state == "WIN":
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    self.state = "MENU"
            return
            
        if self.state != "PLAYING":
            return

        keys = pygame.key.get_pressed()
        self.game_time += 1

        # ★ 실존 우주 이론: 엔트로피 증가 (열적 죽음 가속)
        self.entropy = min(self.entropy_max, self.entropy + self.entropy_rate)
        
        progress = min(1.0, self.game_time / (self.current_chapter.duration * 60))
        # 레벨 보너스: 레벨당 0.4 증가 (완만한 난이도 상승)
        level_bonus = (self.player.level - 1) * 0.4
        # 후반부 폭증 커브
        # 난이도 곡선 대폭 상향 (progress 계수 18.0 -> 25.0, 레벨 보너스 강화)
        self.difficulty = 1.0 + (progress ** 1.2) * 25.0 + (level_bonus * 1.5)

        #  심해 잠수 키 처리 (Z키, diving 챕터 전용)
        is_diving_chapter = "diving" in self.current_chapter.special
        diving_key = keys[pygame.K_z]
        self.player.update_dive(diving_key, is_diving_chapter)

        # 잠수 시 산소 0 데미지 체크
        if self.player.dive_active and self.player.dive_oxygen <= 0:
            if self.notify_timer <= 0:
                self.notify(" 산소 부족! 수면으로 올라오세요!", 60)
            if self.player.health <= 0:
                self._grant_death_rewards()
                return

        # 잠수 중 심해 적 추가 소환
        if self.player.dive_active and self.player.dive_depth > 30:
            self.dive_spawn_timer += 1
            if self.dive_spawn_timer > 120:
                self.dive_spawn_timer = 0
                angle = random.uniform(0,360)
                dist  = random.uniform(200,400)
                sp    = self.player.world_pos + Vector2(math.cos(math.radians(angle))*dist,
                                                         math.sin(math.radians(angle))*dist)
                etype = "deep_angler" if random.random() < 0.6 else "abyss_eel"
                self.enemies.add(Enemy(sp, "PHYSICAL", etype, self.difficulty + self.player.dive_depth/50))
                # 아이템 드롭 (심해 크리스탈)
                if random.random() < 0.3:
                    crystal_pos = self.player.world_pos + Vector2(
                        random.uniform(-150,150), random.uniform(-150,150))
                    self._drop_item_at(crystal_pos, "abyss_crystal")
        else:
            self.dive_spawn_timer = max(0, self.dive_spawn_timer - 1)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_TAB:
                    self.settings_open = not self.settings_open
                    self.settings_sel  = 0

            if self.settings_open:
                self._handle_settings_input(event)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # 무기 인벤토리 슬롯 클릭 확인
                    clicked_wkey = None
                    for wr, wk in self._weapon_inv_slots:
                        if wr.collidepoint(event.pos):
                            clicked_wkey = wk
                            break
                    if clicked_wkey:
                        self.player.weapon_key = clicked_wkey
                        self.player.job_stats["weapon_switches"] += 1
                        self.notify(f"무기: {WEAPONS[clicked_wkey]['name']}", 60)
                    else:
                        self._manual_shoot(event.pos)
                elif event.button == 3:
                    self.player.switch_weapon(1)
                    self.notify(f"무기: {self.player.weapon['name']}", 80)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    self.dimension = "VOID" if self.dimension=="PHYSICAL" else "PHYSICAL"
                    self.player.set_dimension(self.dimension)
                    self._burst(self.player.world_pos,
                                (200,100,255) if self.dimension=="VOID" else (0,200,255),
                                count=20, speed=6)
                    self.notify(f"차원 전환 → {self.dimension}", 80)
                    self._on_dimension_shift()
                    self.player.job_stats["dim_switches"] += 1
                
                #  스킬 사용 [1, 2, 3, 4, 5, 6]
                if event.key == pygame.K_1: self._use_skill(0)
                elif event.key == pygame.K_2: self._use_skill(1)
                elif event.key == pygame.K_3: self._use_skill(2)
                elif event.key == pygame.K_4: self._use_skill(3)
                elif event.key == pygame.K_5: self._use_skill(4)
                elif event.key == pygame.K_6: self._use_skill(5)
                elif event.key == pygame.K_q:
                    self.player.switch_weapon(-1)
                    self.player.job_stats["weapon_switches"] += 1
                    self.notify(f"무기: {self.player.weapon['name']}", 80)
                elif event.key == pygame.K_e:
                    self.player.switch_weapon(1)
                    self.player.job_stats["weapon_switches"] += 1
                    self.notify(f"무기: {self.player.weapon['name']}", 80)
                elif event.key == pygame.K_SPACE:
                    if self.player.try_dash(keys):
                        self.player.job_stats["dash_count"] += 1
                        self._burst(self.player.world_pos, (255,255,255), count=8, speed=5, life=15)
                elif event.key == pygame.K_f and self.player.mode == "SHIP":
                    if len(self.player.unlocked_forms) > 1:
                        self.form_select_active = True
                        self.form_select_idx = self.player.unlocked_forms.index(self.player.ship_form)
                    else:
                        self.notify("해금된 변형 없음. 레벨업 시 획득!", 100)
                #  Z키 안내 알림
                elif event.key == pygame.K_z and not is_diving_chapter:
                    self.notify("이 챕터에서는 잠수 불가! (챕터3·6 전용)", 90)

        if self.settings_open:
            return

        friction = self.current_chapter.friction
        buoyancy = 0
        for f in self.fluids:
            if f.get_world_rect().collidepoint(self.player.world_pos.x, self.player.world_pos.y):
                friction *= 2; buoyancy = f.buoyancy
        if "deep_gravity" in self.current_chapter.special:
            buoyancy += 0.05

        self.player.update(keys, friction, self.current_chapter.mode, self.mouse_pos)
        self.player.world_pos.y += buoyancy

        player_wr = pygame.Rect(self.player.world_pos.x-16, self.player.world_pos.y-16, 32,32)
        for s in self.structures:
            if s.get_world_rect().colliderect(player_wr):
                self.player.world_pos -= self.player.vel
                self.player.vel *= -0.4

        self._update_camera()
        self._try_spawn_blackhole()
        self._update_blackholes()
        
        # ★ 멀티버스 포탈 상호작용 및 애니메이션
        if self.portal_suck_timer > 0:
            self.portal_suck_timer -= 1
            t = 1.0 - (self.portal_suck_timer / 120.0)
            target_pos = self.portal_suck_target.world_pos
            # 플레이어를 포탈 중심으로 흡입 (회전하며 축소되는 느낌)
            self.player.world_pos += (target_pos - self.player.world_pos) * 0.12
            self.player.angle = (self.player.angle + 15) % 360
            if self.portal_suck_timer == 0:
                self._shift_universe(target=self.portal_suck_target.target_universe)
                self.portals.empty()
                self.portal_suck_target = None
            return # 포탈 흡입 중에는 다른 업데이트 중단

        for portal in self.portals:
            portal.update()
            dist = (self.player.world_pos - portal.world_pos).length()
            if dist < 60:
                self.portal_suck_timer = 120
                self.portal_suck_target = portal
                self.screen_shake(30, 120)
                self._burst(portal.world_pos, (255,255,255), count=50, speed=12)

        self.spawn_timer += 1
        # 스폰 속도 향상: lv1=60f(1s), lv10=30f, lv20=10f (최소 4프레임)
        lv = self.player.level
        interval = max(4, 60 - (lv - 1) * 3)
        if self.spawn_timer > interval:
            self.spawn_timer = 0
            # 최대 적 수 상향 (최대 40 -> 60)
            max_enemies = min(60, 8 + lv * 3)
            if len(self.enemies) < max_enemies:
                self._spawn_enemy(progress)

        self.item_timer += 1
        if self.item_timer > 600:
            self.item_timer = 0
            self._drop_random_item()

        # ── 엘리트 서지 웨이브 (레벨 8 이상에서만) ────────────────────
        if self.difficulty >= 2.5 and self.player.level >= 8:
            self.surge_timer += 1
            surge_interval = max(180, int(400 - self.difficulty * 35))
            if self.surge_warning > 0:
                self.surge_warning -= 1
            if self.surge_timer >= surge_interval:
                self.surge_timer = 0
                self._spawn_elite_surge()

        # ── 위협 수준 경고 ──────────────────────────────────────────
        enemy_count = len(self.enemies)
        if enemy_count >= 28 and self.game_time % 120 == 0:
            self.notify(f"⚠ OVERLOAD — 적 {enemy_count}체! 처치하라!", 90)

        self.player.timer += 1
        if self.player.timer > self.player.weapon_cooldown:
            self.player.timer = 0
            self._auto_shoot()

        for comp in self.companions:
            comp.update(self.enemies, self.projectiles, self.dimension, self.camera_offset)

        for ally in self.allies:
            ally.update(self.enemies, self.projectiles, self.dimension, self.camera_offset)

        if self.freeze_timer > 0:
            self.freeze_timer -= 1

        for p in list(self.projectiles):
            p.update()
        for ep in list(self.enemy_projectiles):
            ep.update()

        # 스텔스 체크: 클로킹 중이면 적이 플레이어를 추주하지 않음
        effective_p_pos = self.player.world_pos
        if self.player.skill_stealth_timer > 0:
            effective_p_pos = self.player.world_pos + Vector2(10000, 10000)

        enemy_list = list(self.enemies)
        for enemy in enemy_list:
            if self.freeze_timer > 0 and enemy.special != "phase_boss":
                continue # 보스급 제외 일반 적 정지
            if enemy.dimension_type == self.dimension or self.abyss_active:
                enemy.update(effective_p_pos,
                             enemy_projectiles=self.enemy_projectiles,
                             dimension=self.dimension,
                             all_enemies=enemy_list)
                if enemy.special == "gravity_vacuum":
                    dist = (self.player.world_pos - enemy.world_pos).length()
                    if dist < 400:
                        pull = (enemy.world_pos - self.player.world_pos).normalize() * 1.5
                        self.player.world_pos += pull

        player_wr2 = pygame.Rect(self.player.world_pos.x-14, self.player.world_pos.y-14, 28,28)
        if self.player.skill_titan_timer > 0:
            player_wr2 = pygame.Rect(self.player.world_pos.x-30, self.player.world_pos.y-30, 60,60)
            
        for enemy in list(self.enemies):
            if enemy.dimension_type == self.dimension or self.abyss_active:
                er = pygame.Rect(enemy.world_pos.x-enemy.rect.w//2,
                                 enemy.world_pos.y-enemy.rect.h//2,
                                 enemy.rect.w, enemy.rect.h)
                if er.colliderect(player_wr2):
                    if self.player.skill_titan_timer > 0:
                        enemy.take_damage(50)
                        self._burst(enemy.world_pos, (255,100,0), count=10)
                    elif self.player.invincible <= 0:
                        base_dmg = 20 if enemy.max_hp >= 100 else (10 if enemy.max_hp >= 20 else 5)
                        dmg = base_dmg + getattr(enemy, "dmg_bonus", 0)
                        actual = self.player.take_hit(dmg)
                        if actual > 0:
                            self.player.job_stats["damage_taken"] += actual
                        self.screen_shake(6,8)
                        self.notify(f"피격! HP -{actual}" if actual>0 else "쉴드 흡수!", 50)
        if self.player.invincible > 0:
            self.player.invincible -= 1

        for ep in list(self.enemy_projectiles):
            if ep.dimension == self.dimension or self.abyss_active:
                ep_r = pygame.Rect(ep.world_pos.x-7, ep.world_pos.y-7, 14,14)
                if ep_r.colliderect(player_wr2) and self.player.invincible <= 0:
                    actual = self.player.take_hit(ep.dmg)
                    if actual > 0:
                        self.player.job_stats["damage_taken"] += actual
                    self.screen_shake(5,6)
                    self.notify(f"피격! HP -{actual}" if actual>0 else "쉴드 흡수!", 50)
                    ep.kill()

        for p in list(self.projectiles):
            p_r = pygame.Rect(p.world_pos.x-6, p.world_pos.y-6, 12,12)
            for enemy in list(self.enemies):
                if enemy.dimension_type == p.dimension or self.abyss_active:
                    er = pygame.Rect(enemy.world_pos.x-enemy.rect.w//2,
                                     enemy.world_pos.y-enemy.rect.h//2,
                                     enemy.rect.w, enemy.rect.h)
                    if er.colliderect(p_r):
                        #  약점 시스템 타격 판정
                        is_crit = False
                        if enemy.weak_point and enemy.weak_point.check_hit(p.world_pos, enemy.world_pos):
                            is_crit = True
                            
                        dmg = int(p.dmg * self.player.get_dmg_mult())
                        if is_crit: 
                            dmg *= 3
                            self.notify(" CRITICAL HIT!!", 40)
                            
                        #  뇌창 폭발 처리
                        if getattr(p, "special", None) == "thunder_spear":
                            pos = p.world_pos
                            self._burst(pos, (255,100,0), count=40, speed=10, life=30)
                            self.screen_shake(20, 15)
                            for e_near in list(self.enemies):
                                dist = (e_near.world_pos - pos).length()
                                if dist < 120:
                                    e_near.take_damage(p.dmg)
                                    self._burst(e_near.world_pos, (255,255,255), count=5)
                        
                        if enemy.take_damage(dmg):
                            #  뱀파이어리즘 흡혈 로직
                            if self.player.skill_vamp_timer > 0:
                                v_lvl = self.owned_skills.get("vampirism", 1)
                                if random.random() < (0.3 + v_lvl * 0.1):
                                    self.player.health = min(self.player.max_health, self.player.health + 1 + v_lvl)
                                    self._burst(enemy.world_pos, (255, 0, 0), count=15, speed=8)
                                    self.notify(" 흡혈!", 30)

                            data = ENEMY_DATA.get(enemy.etype, {})
                            col  = data.get("cp",(255,100,0)) if self.dimension=="PHYSICAL" else data.get("cv",(255,0,200))
                            self._burst(enemy.world_pos, col, count=15, speed=5, life=35)
                            #  쥬스 효과 (타격감)
                            shake_pow = 10 if enemy.max_hp >= 20 else 4
                            self.screen_shake(shake_pow, 8 if shake_pow==4 else 12)
                            self.gems.add(Gem(enemy.world_pos, enemy.gem_val))
                            if random.random() < 0.10: self._drop_item_at(enemy.world_pos)
                            combo = self.player.kill_combo()
                            mult  = self.player.get_combo_multiplier()
                            pts   = int(enemy.gem_val * 10 * mult)
                            #  멀티버스 점수 보물 (GOLDEN 현실 보너스)
                            if self.universe_type == "GOLDEN": pts *= 2
                            
                            self.player.score += pts
                            if combo % 5 == 0 and combo >= 5:
                                self.notify(f"COMBO ×{combo}!  ×{mult:.1f}", 90)
                            #  연속킬 streak 이펙트
                            sk = self.player.streak_kills
                            if sk > 0 and sk % 5 == 0:
                                self.streak_flash_timer = 45
                                self.streak_flash_count = sk
                                self._burst(enemy.world_pos, (255,220,0), count=30, speed=8, life=45)
                                self.screen_shake(12, 15)

                            # 전직 통계 추적 — 처치 무기 분류
                            melee_weps = {"laser","shotgun","gatling","shockwave","gomu_gatling"}
                            range_weps = {"sniper","railgun","rocket","void_cannon"}
                            wk = self.player.weapon_key
                            js = self.player.job_stats
                            if wk in melee_weps:
                                js["melee_kills"] += 1
                            elif wk in range_weps:
                                js["range_kills"] += 1
                            js["max_combo"] = max(js["max_combo"], combo)
                            # 흡혈귀: vampirism 활성 처치
                            if self.player.skill_vamp_timer > 0:
                                js["vamp_kills"] += 1
                            # 직업 등급: 처치 수 추적
                            if self.player.job:
                                self.player.job_kills += 1
                                new_tier = self.player.check_job_tier_up()
                                if new_tier is not None:
                                    tier_name = JOB_TIER_DATA["names"][new_tier]
                                    tier_col  = JOB_TIER_DATA["colors"][new_tier]
                                    dmg_m     = JOB_TIER_DATA["dmg_mult"][new_tier]
                                    self.notify(
                                        f"등급 상승! [{self.player.job}] {tier_name}  데미지 ×{dmg_m:.2f}",
                                        180)
                                    self._burst(self.player.world_pos, tier_col, count=40, speed=8, life=50)
                                    self.screen_shake(8, 12)

                            enemy.kill()
                        if not getattr(p, "pierce", False):
                            if enemy.special != "phase_boss":
                                p.kill()
                        break

        for gem in list(self.gems):
            gem.update()
            if (self.player.world_pos - gem.world_pos).length() < 32:
                #  영구 업그레이드 XP 보너스 적용
                xp_gain = gem.value * getattr(self.player, "_xp_upg_mult", 1.0)
                self.player.xp += xp_gain
                self._burst(gem.world_pos, (0,255,150), count=5, speed=3, life=18)
                if self.player.xp >= self.player.xp_to_next:
                    self._trigger_levelup()
                gem.kill()


        for item in list(self.items):
            if not item.update():
                item.kill(); continue
            if (self.player.world_pos - item.world_pos).length() < 26:
                self._apply_item(item.itype)
                self._burst(item.world_pos, ITEM_DATA.get(item.itype,{"color":(255,255,255)})["color"], count=10)
                item.kill()

        self.particles = [p for p in self.particles if p.update()]



        #  멀티버스 업데이트 — 후반부로 갈수록 전환 빨라짐
        self.universe_timer += 1
        dynamic_cycle = max(2400, self.universe_cycle - int(self.difficulty * 180))
        if self.universe_timer >= dynamic_cycle:
            self.universe_timer = 0
            self._shift_universe()

        if self.game_time > self.current_chapter.duration * 60:
            if self.current_chapter == self.chapters.get("0"):
                self.played_job_chapter = True
                self._save_data()
                if not self.job_select_active and not getattr(self.player, "job", None):
                    self._trigger_job_select()
                    return
                if self.job_select_active:
                    return # 전직 선택 화면 전개 대기
                self.high_score = max(self.high_score, self.player.score)
                self.state = "WIN"
                return

            if "job_awakening" in getattr(self.current_chapter, "special", []):
                if not getattr(self.player, "_awaken_triggered", False):
                    self.player.job = None
                    self._trigger_job_select()
                    self.player._awaken_triggered = True
                    return
                if self.job_select_active:
                    return
                self.high_score = max(self.high_score, self.player.score)
                self.state = "WIN"
                return

            if "tier_promotion" in getattr(self.current_chapter, "special", []):
                if not getattr(self.player, "_tier_promoted", False):
                    if hasattr(self.player, "job") and self.player.job:
                        self.player.job_tier = min(4, getattr(self.player, "job_tier", 0) + 1)
                        self.notify(f"직업 승급! 현재 티어: {self.player.job_tier}", 200)
                        self._save_data()
                    self.player._tier_promoted = True
                self.high_score = max(self.high_score, self.player.score)
                self.state = "WIN"
                return

            final_bosses = ["void_god","abyss_sovereign","nexus_overmind","abyssal_tyrant"]
            alive_finals = [e for e in self.enemies if e.etype in final_bosses]
            if alive_finals:
                self.game_time = self.current_chapter.duration * 60
                if self.notify_timer <= 0:
                    boss_name = alive_finals[0].name
                    self.notify(f" {boss_name}를 처치해야 클리어! ", 240)
                return
            if "mega_bosses" in self.current_chapter.special:
                for fb in ["void_god","abyss_sovereign"]:
                    if not any(e.etype == fb for e in self.enemies):
                        angle = random.uniform(0,360)
                        sp = self.player.world_pos + Vector2(
                            math.cos(math.radians(angle))*400,
                            math.sin(math.radians(angle))*400)
                        self.difficulty += 1.0
                        self.enemies.add(Enemy(sp, "PHYSICAL", fb, self.difficulty))
                        self.notify(f" {ENEMY_DATA[fb]['name']} 강제 출현! 처치하라! ", 300)
                        self.screen_shake(25, 30)
                        self.game_time = self.current_chapter.duration * 60
                        return
            else:
                general_final = ["nexus_overmind","abyssal_tyrant"]
                for fb in general_final:
                    if not any(e.etype == fb for e in self.enemies):
                        angle = random.uniform(0,360)
                        sp = self.player.world_pos + Vector2(
                            math.cos(math.radians(angle))*400,
                            math.sin(math.radians(angle))*400)
                        self.difficulty += 1.0
                        self.enemies.add(Enemy(sp, "PHYSICAL", fb, self.difficulty))
                        self.notify(f" {ENEMY_DATA[fb]['name']} 최후의 저항! 처치해야 클리어!", 300)
                        self.screen_shake(20, 25)
                        self.game_time = self.current_chapter.duration * 60
                        return
            self.high_score = max(self.high_score, self.player.score)
            self.state = "WIN"

    def _shift_universe(self, target=None):
        old = self.universe_type
        if target:
            self.universe_type = target
        else:
            choices = [u for u in self.universes.keys() if u != old]
            self.universe_type = random.choice(choices)
            
        u_data = self.universes[self.universe_type]
        self.notify(f" 멀티버스 전이! [{u_data['name']}]", 240)
        self.screen_shake(8, 15)
        self._burst(self.player.world_pos, u_data["color"], count=35, speed=8, life=55)

        # 유니버스 상태 동기화
        if self.player: self.player.multiverse_type = self.universe_type
        for e in self.enemies: e.multiverse_type = self.universe_type

        # 유니버스별 즉각적인 수치 조정
        if self.universe_type == "GOLDEN":
            self.player.health = min(self.player.health, self.player.max_health // 2)
        elif self.universe_type == "GLITCH":
            self.screen_shake(12, 18)

        # 적 인챈트 & 전용 적 소환
        self._enchant_enemies_on_universe_shift()

    # ─────────────────────────────────────
    #  SETTINGS
    # ─────────────────────────────────────
    def _handle_settings_input(self, event):
        if event.type != pygame.KEYDOWN: return
        keys_order = SETTINGS.KEYS_ORDER
        n = len(keys_order)
        if event.key == pygame.K_z:
            # 설정 선택된 항목이 프로필 영역(0,1,2)일 때 이름/랭크 등 변경 사이클
            if self.settings_sel == 0:
                names = ["KIM", "LEE", "PARK", "CHOI", "GHOST", "REAPER"]
                idx = (names.index(self.pilot_name) + 1) % len(names) if self.pilot_name in names else 0
                self.pilot_name = names[idx]; self._save_data()
            elif self.settings_sel == 1:
                ranks = ["RECRUIT", "PILOT", "COMMANDER", "ACE", "VETERAN"]
                idx = (ranks.index(self.pilot_rank) + 1) % len(ranks) if self.pilot_rank in ranks else 0
                self.pilot_rank = ranks[idx]; self._save_data()
            elif self.settings_sel == 2:
                calls = ["RAVEN-01", "PHANTOM", "STRIKER", "NEON-X", "VOID-7"]
                idx = (calls.index(self.pilot_callsign) + 1) % len(calls) if self.pilot_callsign in calls else 0
                self.pilot_callsign = calls[idx]; self._save_data()

        if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
            self.settings_open = False; return
        elif event.key == pygame.K_UP:
            self.settings_sel = (self.settings_sel - 1) % (n + 2 + 3)
        elif event.key == pygame.K_DOWN:
            self.settings_sel = (self.settings_sel + 1) % (n + 2 + 3)
        
        if self.settings_sel >= 3:
            actual_sel = self.settings_sel - 3
            if actual_sel < n:
                key = keys_order[actual_sel]
                label, vmin, vmax, step = SETTINGS.LABELS[key]
                cur = getattr(SETTINGS, key)
                if event.key == pygame.K_LEFT:
                    new_val = round(max(vmin, cur - step), 4)
                    setattr(SETTINGS, key, new_val)
                elif event.key == pygame.K_RIGHT:
                    new_val = round(min(vmax, cur + step), 4)
                    setattr(SETTINGS, key, new_val)
        elif self.settings_sel == n + 3:
            if event.key == pygame.K_RETURN:
                SETTINGS.reset_defaults()
                self.notify("설정 초기화 완료!", 90)
        elif self.settings_sel == n + 4:
            if event.key == pygame.K_RETURN:
                self._try_respec_job()

    def _draw_settings(self):
        ov = pygame.Surface((800, 600), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        self.screen.blit(ov, (0, 0))
        self.draw_text("  게임 설정", (400, 32), 34, (0, 220, 255))
        self.draw_text("↑↓ 항목 이동   ←→ 값 조정   ESC/TAB 닫기   ENTER 리셋(하단)", (400, 62), 14, (140, 160, 200))
        keys_order = SETTINGS.KEYS_ORDER
        n = len(keys_order)
        sections = {
            0: "── COMMANDER PROFILE ([Z]로 변경) ────",
            3: "── SHIP 이동 ──────────────────────",
            7: "── HUMAN 이동 ─────────────────────",
            9: "── 대쉬 ────────────────────────────",
            12: "── 카메라 ──────────────────────────",
        }
        row_h = 42; start_y = 90
        
        #  프로필 렌더링 (설정창 내)
        prof_data = [("NAME", self.pilot_name), ("RANK", self.pilot_rank), ("CALLSIGN", self.pilot_callsign)]
        for i, (label, val) in enumerate(prof_data):
            y = start_y + i * row_h
            if i == 0: self.draw_text(sections[0], (400, y - 10), 12, (70, 90, 120))
            sel = (i == self.settings_sel)
            card_col  = (30, 50, 80) if sel else (15, 20, 35)
            pygame.draw.rect(self.screen, card_col, (60, y, 680, 32), border_radius=6)
            self.draw_text(f"{label}: {val}", (200, y + 16), 16, (255, 255, 255) if sel else (140, 150, 170))
            if sel: self.draw_text("[Z] 키로 변경", (630, y + 16), 12, (0, 200, 255))
        
        # 나머지 설정 (오프셋 3 추가)
        for i, key in enumerate(keys_order):
            y = start_y + (i + 3) * row_h
            if (i + 3) in sections:
                self.draw_text(sections[i], (400, y - 10), 12, (70, 90, 120))
                y += 8
            label, vmin, vmax, step = SETTINGS.LABELS[key]
            cur = getattr(SETTINGS, key)
            sel = (i == self.settings_sel)
            card_col  = (30, 50, 80)  if sel else (15, 20, 35)
            border_col = (0, 200, 255) if sel else (40, 50, 70)
            pygame.draw.rect(self.screen, card_col,  (60, y, 680, 32), border_radius=6)
            pygame.draw.rect(self.screen, border_col, (60, y, 680, 32), 2 if sel else 1, border_radius=6)
            self.draw_text(label, (200, y + 16), 16, (255, 230, 100) if sel else (180, 190, 210))
            bar_x, bar_y, bar_w, bar_h = 360, y + 11, 260, 10
            pygame.draw.rect(self.screen, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            t = (cur - vmin) / max(vmax - vmin, 0.0001)
            fill_w = max(6, int(bar_w * t))
            fill_col = (0, 200, 255) if sel else (0, 130, 180)
            pygame.draw.rect(self.screen, fill_col, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
            hx = bar_x + fill_w
            pygame.draw.circle(self.screen, (255, 255, 255) if sel else (150, 200, 220), (hx, bar_y + 5), 6 if sel else 4)
            if isinstance(step, float):
                val_str = f"{cur:.2f}"
            else:
                val_str = str(int(cur))
            self.draw_text(val_str, (670, y + 16), 16, (255, 255, 200) if sel else (160, 170, 180))
            if sel:
                if isinstance(step, float):
                    self.draw_text(f"[{vmin:.2f}~{vmax:.2f}  step:{step}]", (400, y + 34), 11, (90, 120, 160))
        reset_y = start_y + n * row_h + 6
        sel_reset = (self.settings_sel == n + 3)
        rc = (60, 20, 20) if sel_reset else (25, 15, 15)
        bc = (255, 80, 80) if sel_reset else (80, 40, 40)
        pygame.draw.rect(self.screen, rc, (200, reset_y, 400, 32), border_radius=8)
        pygame.draw.rect(self.screen, bc, (200, reset_y, 400, 32), 2, border_radius=8)
        self.draw_text("[ ENTER ] — 모든 설정 초기화", (400, reset_y + 16), 17,
                       (255, 120, 120) if sel_reset else (160, 80, 80))

        # ── 재전직 버튼 (신전 안내) ──────────────────────────────────
        respec_y = reset_y + 44
        pygame.draw.rect(self.screen, (18, 10, 36), (120, respec_y, 560, 44), border_radius=8)
        pygame.draw.rect(self.screen, (100, 50, 180), (120, respec_y, 560, 44), 1, border_radius=8)
        self.draw_text("전직 재선택 — 미니맵의 ● 전직 신전에서 가능",
                       (400, respec_y + 14), 14, (160, 110, 255))
        self.draw_text(f"비용: {self.RESPEC_GOLD_COST:,} G  또는  {self.RESPEC_DIAMOND_COST:,} D",
                       (400, respec_y + 32), 12, (120, 80, 200))

    # ─────────────────────────────────────
    def _drop_item_at(self, world_pos, forced=None):
        if forced:
            self.items.add(PickupItem(world_pos, forced)); return
        itype = random.choices(
            ["hp","shield","speed","ammo","ship_form","overload","crystal"],
            weights=[0.25, 0.20, 0.15, 0.08, 0.08, 0.07, 0.17])[0]
        self.items.add(PickupItem(world_pos, itype))


    def _drop_random_item(self):
        a = random.uniform(0,360); d = random.uniform(150,400)
        pos = self.player.world_pos + Vector2(math.cos(math.radians(a))*d, math.sin(math.radians(a))*d)
        self._drop_item_at(pos)

    def _apply_item(self, itype):
        if itype == "hp":
            h = 30; self.player.health = min(self.player.max_health, self.player.health+h)
            self.notify(f"HP +{h} 회복!", 90)
        elif itype == "shield":
            self.player.shield = min(self.player.max_shield, self.player.shield+25)
            self.notify("쉴드 충전!", 90)
        elif itype == "speed":
            self.player.speed_boost = 300
            self.notify("속도 부스트 5초!", 90)
        elif itype == "ammo":
            self.player._cd_bonus += 1
            self.notify("사격 속도 +1!", 90)
        elif itype == "ship_form":
            locked = [k for k in SHIP_FORMS if k not in self.player.unlocked_forms]
            if locked:
                f = random.choice(locked)
                self.player.unlocked_forms.append(f)
                self.notify(f"변형 해금: {SHIP_FORMS[f]['name']}! [F]로 변경", 180)
            else:
                self.player._cd_bonus += 1
                self.notify("사격 속도 +1! (모든 변형 해금)", 100)
        #  새 아이템: 심해 크리스탈
        elif itype == "abyss_crystal":
            self.player.health = min(self.player.max_health, self.player.health + 20)
            self.player.shield = min(self.player.max_shield, self.player.shield + 20)
            self.player.dive_oxygen = min(self.player.dive_max_oxygen, self.player.dive_oxygen + 180)
            self.notify(" 심해 크리스탈! HP+20 쉴드+20 산소+3초", 120)
            self._burst(self.player.world_pos, (0,220,255), count=25, speed=6, life=40)
        #  새 아이템: 과부하 코어
        elif itype == "overload":
            self.player.overload_timer = 300   # 5초
            self.notify(" 과부하! 5초간 무적·데미지×2.5·사격×2!", 180)
            self.screen_shake(12, 15)
            self._burst(self.player.world_pos, (255,100,0), count=35, speed=9, life=55)
        #  새 아이템: 차원 크리스탈
        elif itype == "crystal":
            self.crystals += 1
            self.notify("특별 크리스탈 획득! (+1)", 130)
            self._burst(self.player.world_pos, (255,255,255), count=15, speed=5, life=40)
        #  새 아이템: 금화
        elif itype == "gold":
            amt = random.randint(10, 50)
            self.gold += amt
            self.notify(f"금화 획득! (+{amt})", 90)
            self._burst(self.player.world_pos, (255,215,0), count=10, speed=4, life=30)
        #  새 아이템: 다이아몬드
        elif itype == "diamond":
            self.diamonds += 1
            self.notify("다이아몬드 발견! (+1)", 150)
            self._burst(self.player.world_pos, (0,191,255), count=20, speed=6, life=50)



    # ─────────────────────────────────────
    def _spawn_elite_surge(self):
        """주기적으로 강적 무리를 한꺼번에 소환 (서지 웨이브)"""
        diff = self.difficulty
        # 서지 강도에 따라 적 선택
        if diff >= 10:
            pool = ["mutant_void", "mutant_sentinel", "mutant_drone", "energy_cursed", "spiral_master"]
            count = random.randint(4, 6)
        elif diff >= 6:
            pool = ["mutant_drone", "mutant_lurker", "elite_enforcer", "void_stinger", "blink_striker"]
            count = random.randint(3, 5)
        else:
            pool = ["elite_enforcer", "void_weaver", "shadow_lurker", "hunter_drone", "blink_striker"]
            count = random.randint(3, 4)

        # 유니버스 전용 적도 섞기
        uni_elites = {
            "CYBER": "cyber_enforcer", "ABYSSAL": "abyss_specter",
            "GOLDEN": "golden_golem",  "GLITCH":  "glitch_ghost"
        }
        if self.universe_type in uni_elites:
            pool.append(uni_elites[self.universe_type])

        surge_label = {2: "소규모", 3: "중규모", 4: "대규모", 5: "최대"}.get(
            min(5, max(2, count)), "대규모")
        self.notify(f"⚠  {surge_label} 서지 웨이브! 엘리트 {count}체 출현!", 180)
        self.surge_warning = 180
        self.screen_shake(12, 20)

        for i in range(count):
            angle = random.uniform(0, 360)
            dist  = random.uniform(350, 550)
            sp    = self.player.world_pos + Vector2(
                math.cos(math.radians(angle)), math.sin(math.radians(angle))) * dist
            etype = random.choice(pool)
            dim   = random.choice(["PHYSICAL", "VOID"])
            e = Enemy(sp, dim, etype, diff + 1.5)
            e.multiverse_type = self.universe_type
            self.enemies.add(e)

        self._burst(self.player.world_pos, (255, 80, 80), count=50, speed=12, life=50)

    # ─────────────────────────────────────
    def _spawn_enemy(self, progress):
        # 레벨이 높으면 더 강한 적이 빨리 나타나도록 함
        effective_progress = max(progress, (self.player.level - 1) / 30.0)
        progress = effective_progress

        angle = random.uniform(0,360)
        dist  = random.uniform(420,620)
        sp    = self.player.world_pos + Vector2(math.cos(math.radians(angle)),
                                                 math.sin(math.radians(angle))) * dist
        dim = random.choice(["PHYSICAL","VOID"])
        ch  = self.current_chapter

        if "mega_bosses" in ch.special:
            mega = ["void_god","abyss_sovereign"]
            for mb in mega:
                bp = ENEMY_DATA[mb]["spawn_progress"]
                if progress >= bp and not any(e.etype==mb for e in self.enemies):
                    self.enemies.add(Enemy(sp, dim, mb, self.difficulty))
                    self.notify(f" {ENEMY_DATA[mb]['name']} 출현! ", 250)
                    self.screen_shake(20,25); return

        boss_types = ["nexus_overmind","abyssal_tyrant"]
        for bt in boss_types:
            bp = ENEMY_DATA[bt]["spawn_progress"]
            if progress >= bp and not any(e.etype==bt for e in self.enemies):
                self.enemies.add(Enemy(sp, dim, bt, self.difficulty))
                self.notify(f" {ENEMY_DATA[bt]['name']} 출현!", 200)
                self.screen_shake(15,20); return

        # 중간 보스는 레벨 10 이상에서만 등장
        if self.player.level >= 10:
            mid_bosses = [("echo_wraith",0.70),("dreadnought_construct",0.50),("anomaly_core",0.25)]
            if ch.enemy_set == "abyss":
                mid_bosses = [("abyss_leviathan",0.55),("abyss_hydra",0.40),("anomaly_core",0.25)]
            elif ch.enemy_set == "void":
                mid_bosses = [("null_colossus",0.60),("echo_wraith",0.40)]
            for mbt, mp in mid_bosses:
                if progress >= mp and not any(e.etype==mbt for e in self.enemies):
                    self.enemies.add(Enemy(sp, dim, mbt, self.difficulty))
                    self.notify(f" {ENEMY_DATA[mbt]['name']} 등장!", 160)
                    self.screen_shake(10,12); return

        abyss_pool = ["abyss_eel","depth_guardian","leviathan_eye","basic_drone","deep_angler"]
        void_pool  = ["null_fragment","void_titan","echo_phantom","glitcher"]

        # 레벨 기반 일반 적 풀 (낮은 레벨엔 쉬운 적만)
        lv = self.player.level
        if lv <= 2:
            normal_pool = ["basic_drone", "swarm_organism"]
        elif lv <= 4:
            normal_pool = ["basic_drone", "swarm_organism", "glitcher", "plasma_fly"]
        elif lv <= 7:
            normal_pool = ["basic_drone", "swarm_organism", "glitcher",
                           "hunter_drone", "null_fragment", "plasma_fly"]
        elif lv <= 10:
            normal_pool = ["glitcher", "hunter_drone", "null_fragment",
                           "sentinel", "sniper_node", "shadow_lurker"]
        elif lv <= 13:
            normal_pool = ["hunter_drone", "sentinel", "sniper_node",
                           "elite_enforcer", "void_weaver", "shadow_lurker", "void_stinger"]
        else:
            normal_pool = ["basic_drone","swarm_organism","glitcher","hunter_drone",
                           "sentinel","sniper_node","elite_enforcer","void_weaver",
                           "corrupted_sentry","shadow_lurker"]

        # ★ 멀티버스 기반 풀 선정
        universe_p = {
            "PRIME": normal_pool,
            "VOID": void_pool,
            "ABYSSAL": abyss_pool,
            "GOLDEN": normal_pool + ["swarm_organism", "basic_drone"],
            "GLITCH": void_pool + ["glitcher", "corrupted_sentry", "shadow_lurker"]
        }.get(self.universe_type, normal_pool)

        if ch.enemy_set == "abyss":
            pool = list(set(universe_p + abyss_pool))
        elif ch.enemy_set == "void":
            pool = list(set(universe_p + void_pool))
        elif ch.enemy_set == "all":
            pool = list(set(normal_pool + abyss_pool + void_pool))
        else:
            pool = list(set(universe_p))

        r = random.random()
        if progress > 0.7 and r < 0.12:
            hard_pool = [p for p in pool if ENEMY_DATA.get(p,{}).get("hp",1)>=3]
            etype = random.choice(hard_pool) if hard_pool else random.choice(pool or ["basic_drone"])
        elif progress > 0.5 and r < 0.22:
            etype = random.choice(pool[len(pool)//2:] or pool or ["basic_drone"])
        elif r < 0.38:
            sw = "swarm_organism" if ch.enemy_set not in ("abyss","void") else (pool[0] if pool else "basic_drone")
            for _ in range(5):
                off = Vector2(random.uniform(-45,45), random.uniform(-45,45))
                new_e = Enemy(sp+off, dim, sw, self.difficulty)
                new_e.multiverse_type = self.universe_type
                self.enemies.add(new_e)
            return
        else:
            etype = random.choice(pool or ["basic_drone"])

        new_enemy = Enemy(sp, dim, etype, self.difficulty)
        new_enemy.multiverse_type = self.universe_type
        self.enemies.add(new_enemy)

    # ─────────────────────────────────────
    def _manual_shoot(self, screen_pos):
        w    = self.player.weapon
        dim  = self.dimension
        col  = w["color_p"] if dim=="PHYSICAL" else w["color_v"]
        fire_dir = self.player.get_fire_direction(screen_pos)
        for _ in range(w["count"]):
            sa  = random.uniform(-w["spread"]/2, w["spread"]/2)
            rad = math.radians(sa)
            rotated = Vector2(fire_dir.x*math.cos(rad)-fire_dir.y*math.sin(rad),
                              fire_dir.x*math.sin(rad)+fire_dir.y*math.cos(rad))
            self.projectiles.add(Projectile(self.player.world_pos, rotated, dim,
                                            game=self,
                                            color_override=col, speed=w["speed"],
                                            dmg=w["dmg"], is_direction=True, size=w["size"]))
        self.player.timer = 0
        self._burst(self.player.world_pos, col, count=4, speed=3, life=10)

    def _auto_shoot(self):
        w   = self.player.weapon
        dim = self.dimension
        col = w["color_p"] if dim=="PHYSICAL" else w["color_v"]
        fire_dir = self.player.get_fire_direction(self.mouse_pos)
        for _ in range(w["count"]):
            sa  = random.uniform(-w["spread"]/2, w["spread"]/2)
            rad = math.radians(sa)
            rotated = Vector2(fire_dir.x*math.cos(rad)-fire_dir.y*math.sin(rad),
                              fire_dir.x*math.sin(rad)+fire_dir.y*math.cos(rad))
            self.projectiles.add(Projectile(self.player.world_pos, rotated, dim,
                                            game=self,
                                            color_override=col, speed=w["speed"],
                                            dmg=w["dmg"], is_direction=True, size=w["size"]))
        self.player.timer = 0

    # ─────────────────────────────────────
    def _trigger_levelup(self):
        self.player.level      += 1
        self.player.xp          = 0
        self.player.xp_to_next += 8
        heal = 25
        self.player.health = min(self.player.max_health, self.player.health+heal)
        self.notify(f"LEVEL UP!  LV {self.player.level}  HP +{heal}", 100)
        self._burst(self.player.world_pos, (255,230,50), count=30, speed=7, life=50)

        locked_w = [w for w in WEAPON_ORDER if w not in self.player.unlocked_weapons]
        locked_f = [f for f in SHIP_FORMS   if f not in self.player.unlocked_forms]
        choices  = []
        if locked_f: choices.append(("form", locked_f[0]))
        if locked_w: choices.append(("weapon", locked_w[0]))
        choices.append(("stat","cooldown"))
        choices.append(("stat","maxhp"))
        choices.append(("stat","robot"))
        random.shuffle(choices)
        self.levelup_choices = choices[:3]
        self.levelup_active  = True

        # 레벨 15: 전직 퀘스트 트리거
        if self.player.level == 15 and not getattr(self.player, "job", None):
            self._trigger_job_select()
            return  # 레벨업 선택창 대신 전직 창 표시

        # ★ 5레벨마다 멀티버스 전이 포탈 생성
        if self.player.level % 5 == 0:
            angle = random.uniform(0, 360)
            dist  = 300
            pos   = self.player.world_pos + Vector2(math.cos(math.radians(angle))*dist, 
                                                   math.sin(math.radians(angle))*dist)
            # 현재 유니버스가 아닌 다른 유니버스 선택
            choices = [u for u in self.universes.keys() if u != self.universe_type]
            target_u = random.choice(choices)
            self.portals.add(Portal(pos, target_universe=target_u))
            self.notify(f" {target_u} 차원으로 통하는 포탈 발생! ", 180)
            self.screen_shake(15, 20)

    def _apply_levelup_choice(self, idx):
        if idx >= len(self.levelup_choices): return
        ctype, cval = self.levelup_choices[idx]
        if ctype == "weapon":
            self.player.unlocked_weapons.append(cval)
            self.player.weapon_key = cval
            self.notify(f"무기 해금: {WEAPONS[cval]['name']}!", 150)
        elif ctype == "form":
            self.player.unlocked_forms.append(cval)
            self.notify(f"변형 해금: {SHIP_FORMS[cval]['name'].split('(')[0]}! [F]로 변경", 160)
        elif ctype == "stat":
            if cval == "cooldown":
                self.player._cd_bonus += 1
                self.notify("사격 속도 +1!", 120)
            elif cval == "maxhp":
                self.player.max_health += 25
                self.player.health = min(self.player.max_health, self.player.health+25)
                self.player.max_shield += 10
                self.notify("최대 HP +25  쉴드 +10!", 130)
            elif cval == "robot":
                types = ["ATTACKER", "STRIKER", "GUARD"]
                owned_types = [c.drone_type for c in self.companions if isinstance(c, RobotCompanion)]
                available = [t for t in types if t not in owned_types]
                
                if available:
                    new_t = random.choice(available)
                    self.companions.add(RobotCompanion(self.player, new_t))
                    self.notify(f"드론 유닛 배치: {new_t}!", 160)
                else:
                    # 모든 종류의 드론이 있으면 화력 강화
                    self.player._cd_bonus += 1
                    self.notify("드론 화력 네트워크 최적화 (사격 속도 +1)", 140)
        self.levelup_active = False

    # ─────────────────────────────────────
    #  JOB SELECT (전직 퀘스트)
    # ─────────────────────────────────────
    def _trigger_job_select(self):
        """플레이 스타일을 분석해 상위 3개 직업을 제시"""
        from entities import JOB_DATA
        js = self.player.job_stats
        # 플레이 스타일 점수 계산
        scores = {
            "전사":    js["melee_kills"]    * 2,
            "저격수":  js["range_kills"]    * 3,
            "파일럿":  js["dash_count"]     * 3 + js["dim_switches"] * 1,
            "마법사":  js["skill_uses"]     * 4,
            "흡혈귀":  js["vamp_kills"]     * 6,
            "기계공":  js["weapon_switches"]* 5,
            "탱커":    js["damage_taken"]  // 8,
            "광속":    js["dash_count"]     * 5,
            "차원술사":js["dim_switches"]   * 10,
            "학살자":  js["max_combo"]      * 8,
        }
        
        # 버틴 시간과 게임 내 활약(킬, 점수)을 바탕으로 가산점 풀 생성
        survived_seconds = self.game_time // 60
        kill_bonus = self.player.kill_count * 2
        score_bonus = self.player.score // 500
        
        # 재전직 등 게임을 오래 진행했을 수록 고착화된 스탯을 역전할 수 있는 보너스 부여
        is_reclass = getattr(self, "played_job_chapter", False)
        multiplier = 3.0 if is_reclass else 1.0
        bonus_pool = int((survived_seconds + kill_bonus + score_bonus) * multiplier)
        
        # 다양한 클래스로 바꿀 수 있도록 각 직업 점수에 무작위 보너스 가산
        if bonus_pool > 0:
            for job in scores.keys():
                scores[job] += random.randint(0, bonus_pool)

        sorted_jobs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        self.job_select_choices = [j for j, _ in sorted_jobs[:3]]
        self.job_select_active  = True
        self.job_select_timer   = 0
        self.levelup_active     = False
        self.notify(" 전직 의식 — 당신의 플레이 스타일이 직업을 결정합니다!", 200)

    def _apply_job(self, idx):
        from entities import JOB_DATA
        if idx >= len(self.job_select_choices): return
        jkey  = self.job_select_choices[idx]
        jdata = JOB_DATA[jkey]
        self.player.apply_job(jkey, jdata)
        self.job_select_active = False
        # 화려한 연출
        self._burst(self.player.world_pos, jdata["color"], count=60, speed=10, life=70)
        self.screen_shake(10, 15)
        self.notify(f"전직 완료! [{jdata['name']}]  {jdata['buff']}", 260)

    RESPEC_GOLD_COST    = 5_000_000
    RESPEC_DIAMOND_COST = 1_000

    def _do_respec_via_chapter(self, currency="gold"):
        if currency == "gold":
            if self.gold < self.RESPEC_GOLD_COST:
                self.notify(f"골드 부족! (필요: {self.RESPEC_GOLD_COST:,} G)", 120)
                self.respec_confirm_active = False
                return
            self.gold -= self.RESPEC_GOLD_COST
        else:
            if self.diamonds < self.RESPEC_DIAMOND_COST:
                self.notify(f"다이아 부족! (필요: {self.RESPEC_DIAMOND_COST:,} D)", 120)
                self.respec_confirm_active = False
                return
            self.diamonds -= self.RESPEC_DIAMOND_COST
        self.respec_confirm_active = False
        self.respec_in_progress    = True
        self.played_job_chapter    = False
        self.start_game("0")

    def _try_respec_job(self, currency="gold"):
        if not getattr(self.player, "job", None):
            self.notify("전직 후에 재선택 가능합니다!", 90)
            return
        if currency == "gold":
            if self.gold < self.RESPEC_GOLD_COST:
                self.notify(f"골드 부족! (필요: {self.RESPEC_GOLD_COST:,} G)", 120)
                return
            self.gold -= self.RESPEC_GOLD_COST
            self.notify(f"재전직 개시! -{self.RESPEC_GOLD_COST:,} G", 120)
        else:
            if self.diamonds < self.RESPEC_DIAMOND_COST:
                self.notify(f"다이아 부족! (필요: {self.RESPEC_DIAMOND_COST:,} D)", 120)
                return
            self.diamonds -= self.RESPEC_DIAMOND_COST
            self.notify(f"재전직 개시! -{self.RESPEC_DIAMOND_COST:,} D", 120)
        self.settings_open = False
        self.respec_dialog_open = False
        self.respec_confirm_active = False
        self._trigger_job_select()

    def _handle_respec_dialog_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.respec_dialog_open = False
        elif event.key == pygame.K_g:
            self._try_respec_job("gold")
        elif event.key == pygame.K_d:
            self._try_respec_job("diamond")

    def _draw_respec_dialog(self):
        """전직 신전 재전직 확인 다이얼로그"""
        ov = pygame.Surface((800, 600), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        self.screen.blit(ov, (0, 0))

        # 패널
        pw, ph = 520, 280
        px, py = 400 - pw // 2, 300 - ph // 2
        pygame.draw.rect(self.screen, (10, 8, 28), (px, py, pw, ph), border_radius=14)
        pygame.draw.rect(self.screen, (140, 60, 255), (px, py, pw, ph), 2, border_radius=14)

        pulse = 0.5 + 0.5 * math.sin(self.game_time * 0.07)
        title_col = (int(200 + 55 * pulse), 150, 255)
        self.draw_text("✦  전직 신전  ✦", (400, py + 30), 28, title_col)
        self.draw_text("재전직 비용을 선택하세요", (400, py + 62), 15, (180, 180, 220))

        job_name = self.player.job or "없음"
        tier_idx = getattr(self.player, "job_tier", 0)
        tier_name = JOB_TIER_DATA["names"][tier_idx]
        tier_col  = JOB_TIER_DATA["colors"][tier_idx]
        self.draw_text(f"현재 직업: {job_name}  [{tier_name}]", (400, py + 90), 14, tier_col)

        # 골드 버튼
        g_can = self.gold >= self.RESPEC_GOLD_COST
        g_col_bg = (30, 50, 20) if g_can else (40, 20, 20)
        g_col_bd = (80, 220, 80) if g_can else (100, 60, 60)
        g_col_tx = (140, 255, 140) if g_can else (160, 80, 80)
        pygame.draw.rect(self.screen, g_col_bg, (px + 30, py + 118, pw - 60, 52), border_radius=8)
        pygame.draw.rect(self.screen, g_col_bd, (px + 30, py + 118, pw - 60, 52), 2, border_radius=8)
        self.draw_text(f"[G]  골드 {self.RESPEC_GOLD_COST:,} G  (보유: {self.gold:,} G)",
                       (400, py + 144), 15, g_col_tx)

        # 다이아 버튼
        d_can = self.diamonds >= self.RESPEC_DIAMOND_COST
        d_col_bg = (20, 30, 55) if d_can else (40, 20, 20)
        d_col_bd = (80, 160, 255) if d_can else (100, 60, 60)
        d_col_tx = (140, 200, 255) if d_can else (160, 80, 80)
        pygame.draw.rect(self.screen, d_col_bg, (px + 30, py + 180, pw - 60, 52), border_radius=8)
        pygame.draw.rect(self.screen, d_col_bd, (px + 30, py + 180, pw - 60, 52), 2, border_radius=8)
        self.draw_text(f"[D]  다이아 {self.RESPEC_DIAMOND_COST:,} D  (보유: {self.diamonds:,} D)",
                       (400, py + 206), 15, d_col_tx)

        self.draw_text("[ESC] 취소", (400, py + 256), 12, (120, 120, 160))

    # ─────────────────────────────────────
    #  SHOP LOGIC
    # ─────────────────────────────────────
    def _handle_shop_input(self, event):
        from entities import PERSISTENT_UPGRADES, ACTIVE_SKILLS, JOB_DATA
        
        # 전체 리스트 동적 재구성 (draw_shop과 일치해야 함)
        upgrades = [(k, v, False) for k, v in PERSISTENT_UPGRADES.items()]
        active_skills = []
        passive_skills = []
        for k, v in ACTIVE_SKILLS.items():
            if v.get("type") == "passive":
                passive_skills.append((k, v, True))
            else:
                active_skills.append((k, v, True))
        
        all_items = upgrades + active_skills + passive_skills
        
        if self.shop_tab == 1:
            # 직업 마켓 전용 키 핸들링
            jobs = list(JOB_DATA.keys())
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.job_market_sel = (self.job_market_sel - 2) % len(jobs)
                    # 자동 스크롤
                    r = self.job_market_sel // 2
                    target_y = 185 + r * 92 + self.shop_scroll_y
                    if target_y < 190: self.shop_scroll_y += 92
                    elif target_y > 500: self.shop_scroll_y -= 92
                elif event.key == pygame.K_DOWN:
                    self.job_market_sel = (self.job_market_sel + 2) % len(jobs)
                    # 자동 스크롤
                    r = self.job_market_sel // 2
                    target_y = 185 + r * 92 + self.shop_scroll_y
                    if target_y < 190: self.shop_scroll_y += 92
                    elif target_y > 500: self.shop_scroll_y -= 92
                elif event.key == pygame.K_LEFT:
                    self.job_market_sel = (self.job_market_sel - 1) % len(jobs)
                elif event.key == pygame.K_RIGHT:
                    self.job_market_sel = (self.job_market_sel + 1) % len(jobs)
                elif event.key == pygame.K_PAGEUP:
                    self.shop_scroll_y = min(0, self.shop_scroll_y + 200)
                elif event.key == pygame.K_PAGEDOWN:
                    from entities import JOB_DATA
                    rows = (len(JOB_DATA) + 1) // 2
                    max_scroll = -max(0, rows * 92 - 340)
                    self.shop_scroll_y = max(max_scroll, self.shop_scroll_y - 200)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._buy_job(jobs[self.job_market_sel], "gold")
                elif event.key == pygame.K_d:
                    self._buy_job(jobs[self.job_market_sel], "diamond")
                elif event.key in (pygame.K_j, pygame.K_m):
                    self.shop_tab = 0; self.shop_sel = 0
                elif event.key == pygame.K_ESCAPE:
                    self.state = "MENU"
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.shop_sel = (self.shop_sel - 1) % len(all_items)
                # 자동 스크롤 (단순화)
                if self.shop_sel * 35 + self.shop_scroll_y < 0: self.shop_scroll_y += 35
            elif event.key == pygame.K_DOWN:
                self.shop_sel = (self.shop_sel + 1) % len(all_items)
                if self.shop_sel * 35 + self.shop_scroll_y > 350: self.shop_scroll_y -= 35
            elif event.key == pygame.K_LEFT:
                self.shop_sel = (self.shop_sel - 2) % len(all_items)
            elif event.key == pygame.K_RIGHT:
                self.shop_sel = (self.shop_sel + 2) % len(all_items)
            elif event.key == pygame.K_PAGEUP:
                self.shop_scroll_y = min(0, self.shop_scroll_y + 200)
            elif event.key == pygame.K_PAGEDOWN:
                rows = (len(all_items) + 1) // 2 + 3 
                max_scroll = -max(0, rows * 68 - 380)
                self.shop_scroll_y = max(max_scroll, self.shop_scroll_y - 200)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                sel_key, data, is_skill = all_items[self.shop_sel]
                
                if not is_skill:
                    upg = data
                    cur_lvl = self.upgrades.get(sel_key, 0)
                    cost = upg["cost"] * (cur_lvl + 1)
                    currency = upg.get("currency", "gold")
                    
                    if cur_lvl < upg["max_lvl"]:
                        if (currency == "gold" and self.gold >= cost) or \
                           (currency == "diamond" and self.diamonds >= cost):
                            if currency == "gold": self.gold -= cost
                            else: self.diamonds -= cost
                            self.upgrades[sel_key] += 1
                            self._apply_permanent_boost(sel_key)
                            self._save_data()
                            self.notify(f"업그레이드 완료: {upg['name']} Lv.{self.upgrades[sel_key]}", 120)
                        else:
                            self.notify(f"자원이 부족합니다! ({currency.upper()} 부족)", 100)
                    else:
                        self.notify("최대 레벨 도달!", 100)
                
                else:
                    skill = data
                    cur_lvl = self.owned_skills.get(sel_key, 0)
                    
                    if cur_lvl < skill["max_lvl"]:
                        cost = skill["cost"] * (cur_lvl + 1)
                        currency = skill.get("currency", "gold")
                        
                        if (currency == "gold" and self.gold >= cost) or \
                           (currency == "diamond" and self.diamonds >= cost):
                            if currency == "gold": 
                                self.gold -= cost
                            else: 
                                self.diamonds -= cost
                                
                            if cur_lvl == 0:
                                self.owned_skills[sel_key] = 1
                                # 자동 장착: 슬롯에 빈 자리가 있으면 장착
                                if len(self.equipped_skills) < 6:
                                    self.equipped_skills.append(sel_key)
                                    self.notify(f"스킬 해금 + 장착: {skill['name']}!", 150)
                                else:
                                    self.notify(f"스킬 해금: {skill['name']}! (슬롯 꽉참 - [I]키로 관리)", 150)
                                if self.player:
                                    self.player.active_skills = list(self.equipped_skills)
                            else:
                                self.owned_skills[sel_key] += 1
                                self.notify(f"스킬 레벨업: {skill['name']} Lv.{self.owned_skills[sel_key]}", 150)
                            
                            self._save_data()
                        else:
                            self.notify(f"자원이 부족합니다! ({currency.upper()} 부족)", 100)
                    else:
                        self.notify("최대 레벨 도달!", 100)
            
            # ★ [E] 키: 스킬 장착/해제 토글
            elif event.key == pygame.K_e:
                sel_key, data, is_skill = all_items[self.shop_sel]
                if is_skill and self.owned_skills.get(sel_key, 0) > 0:
                    if sel_key in self.equipped_skills:
                        self.equipped_skills.remove(sel_key)
                        self.notify(f"스킬 해제: {data['name']}", 100)
                    elif len(self.equipped_skills) < 6:
                        self.equipped_skills.append(sel_key)
                        self.notify(f"스킬 장착: {data['name']}!", 100)
                    else:
                        self.notify("슬롯이 꽉 찼습니다! 다른 스킬을 먼저 해제하세요.", 100)
                    if self.player:
                        self.player.active_skills = list(self.equipped_skills)
                    self._save_data()
            
            # ★ [I] 키: 스킬 관리 화면 토글
            elif event.key == pygame.K_i:
                self.skill_manage_open = not self.skill_manage_open
                self.skill_manage_sel = 0
                            
            elif event.key == pygame.K_ESCAPE:
                if self.skill_manage_open:
                    self.skill_manage_open = False
                else:
                    self.state = "MENU"
            elif event.key in (pygame.K_j, pygame.K_m):
                # J/M 키: 직업마켓 탭 전환
                self.shop_tab = 1 - self.shop_tab
                self.job_market_sel = 0
                self.shop_scroll_y = 0  # 탭 전환 시 스크롤 초기화

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            # 탭 전환 버튼 (시각적 위치 100~400, 400~700)
            tab_upgrade_btn = pygame.Rect(100, 145, 300, 30)
            tab_job_btn     = pygame.Rect(400, 145, 300, 30)
            if tab_upgrade_btn.collidepoint(mx, my):
                if self.shop_tab != 0:
                    self.shop_tab = 0; self.shop_scroll_y = 0
                return
            if tab_job_btn.collidepoint(mx, my):
                if self.shop_tab != 1:
                    self.shop_tab = 1; self.job_market_sel = 0; self.shop_scroll_y = 0
                return
            # 직업마켓 탭일 때 직업 카드 클릭
            if self.shop_tab == 1:
                self._handle_job_market_click(mx, my)

    # ──────────────────────────────────────────────────────────
    #  직업 마켓 (JOB MARKET)
    # ──────────────────────────────────────────────────────────

    # 직업별 가격 테이블 (gold, diamonds)
    JOB_PRICES = {
        "전사":     {"gold": 80_000,  "dia": 120},
        "저격수":   {"gold": 90_000,  "dia": 130},
        "파일럿":   {"gold": 95_000,  "dia": 140},
        "마법사":   {"gold": 110_000, "dia": 160},
        "흡혈귀":   {"gold": 130_000, "dia": 200},
        "기계공":   {"gold": 120_000, "dia": 180},
        "탱커":     {"gold": 100_000, "dia": 150},
        "광속":     {"gold": 105_000, "dia": 155},
        "차원술사": {"gold": 150_000, "dia": 250},
        "학살자":   {"gold": 140_000, "dia": 220},
    }

    def _buy_job(self, jkey, currency="gold"):
        """골드 또는 다이아로 원하는 직업을 즉시 구매 또는 이미 소유한 직업 장착"""
        from entities import JOB_DATA
        if jkey not in JOB_DATA:
            return
        
        price_info = self.JOB_PRICES.get(jkey, {"gold": 100_000, "dia": 200})
        is_owned = jkey in getattr(self, "owned_jobs", ["전사"])
        cost = 0

        if not is_owned:
            if currency == "gold":
                cost = price_info["gold"]
                if self.gold < cost:
                    self.notify(f"골드 부족! 필요: {cost:,} G", 120)
                    return
                self.gold -= cost
            else:
                cost = price_info["dia"]
                if self.diamonds < cost:
                    self.notify(f"다이아 부족! 필요: {cost:,} D", 120)
                    return
                self.diamonds -= cost
            
            if not hasattr(self, "owned_jobs"): self.owned_jobs = ["전사"]
            self.owned_jobs.append(jkey)
            self.notify(f"직업 해금 완료! [{JOB_DATA[jkey]['name']}]", 120)
        else:
            self.notify(f"직업 장착: {JOB_DATA[jkey]['name']}", 120)

        # 직업 적용 (플레이어가 없으면 saved_job 에 저장)
        if self.player:
            self.player.apply_job(jkey, JOB_DATA[jkey])
        self.saved_job = jkey
        self.played_job_chapter = True

        # 효과 연출
        if self.player:
            self._burst(self.player.world_pos, JOB_DATA[jkey]["color"], count=50, speed=9, life=60)
        self.screen_shake(8, 10)
        
        if not is_owned:
            cur_icon = "G" if currency == "gold" else "D"
            self.notify(f"구매 완료! -{cost:,}{cur_icon}", 180)
        
        self._save_data()

    def _handle_job_market_click(self, mx, my):
        """직업 마켓 카드 클릭 → 골드 구매 (우클릭은 다이아)"""
        from entities import JOB_DATA
        jobs = list(JOB_DATA.keys())
        cols, card_w, card_h = 2, 350, 84
        x0, y0, x_gap, y_gap = 40, 185 + self.shop_scroll_y, 365, 92
        for i, jkey in enumerate(jobs):
            r = i // cols; c = i % cols
            card = pygame.Rect(x0 + c * x_gap, y0 + r * y_gap, card_w, card_h)
            if card.collidepoint(mx, my):
                self._buy_job(jkey, "gold")
                return

    def _draw_job_market(self):
        """직업 마켓 탭 UI"""
        from entities import JOB_DATA
        mx, my = pygame.mouse.get_pos()
        jobs = list(JOB_DATA.keys())
        curr_job = (self.player.job if self.player else None) or getattr(self, "saved_job", None)

        cols, card_w, card_h = 2, 350, 84
        x0, y0, x_gap, y_gap = 40, 185 + self.shop_scroll_y, 365, 92

        # 마켓 전용 헤더 (스크롤 영향을 받지 않음)
        self.draw_text("JOB MARKET — 직업 즉시 구매", (400, 170), 18, (255, 220, 80))
        
        # 클리핑 설정
        self.screen.set_clip(pygame.Rect(0, 180, 800, 530 - 180))

        for i, jkey in enumerate(jobs):
            r = i // cols; c = i % cols
            card = pygame.Rect(x0 + c * x_gap, y0 + r * y_gap, card_w, card_h)
            jd = JOB_DATA[jkey]
            price = self.JOB_PRICES.get(jkey, {"gold": 100_000, "dia": 200})
            is_active = (jkey == curr_job)
            is_owned  = jkey in self.owned_jobs
            hov = card.collidepoint(mx, my)
            sel = (i == self.job_market_sel)

            # 배경
            bg = (25, 35, 55) if hov or sel else (15, 18, 32)
            pygame.draw.rect(self.screen, bg, card, border_radius=10)
            border_col = jd["color"] if is_active else ((255, 255, 100) if sel else (60, 70, 110))
            bw = 2 if is_active or sel else 1
            pygame.draw.rect(self.screen, border_col, card, bw, border_radius=10)

            # 소유/장착 상태 표시
            if is_active:
                tag_surf = pygame.Surface((50, 18), pygame.SRCALPHA)
                tag_surf.fill((0, 255, 120, 180))
                self.screen.blit(tag_surf, (card.right - 52, card.top + 2))
                self.draw_text("사용중", (card.right - 27, card.top + 11), 11, (0, 0, 0))
            elif is_owned:
                self.draw_text("장착가능", (card.right - 10, card.top + 11), 10, (100, 255, 150), align="right")

            # 직업명 & 설명 (글씨가 다 보이게 조정)
            cy = card.centery
            self.draw_text(jkey, (card.left + 18, cy - 18), 20, jd["color"], align="left")
            
            buff_txt = f"▲ {jd.get('buff', '')}"
            nerf_txt = f"▼ {jd.get('nerf', '')}"
            self.draw_text(buff_txt, (card.left + 18, cy + 6), 11, (100, 255, 150), align="left")
            self.draw_text(nerf_txt, (card.left + 18, cy + 22), 11, (255, 150, 150), align="left")

            # 가격 (미소유 시에만 표시)
            if not is_owned:
                g_ok = self.gold >= price["gold"]
                d_ok = self.diamonds >= price["dia"]
                g_col = (255, 230, 80) if g_ok else (255, 80, 80)
                d_col = (80, 210, 255) if d_ok else (255, 80, 80)
                self.draw_text(f"{price['gold']:,}G", (card.right - 10, cy - 10), 12, g_col, align="right")
                self.draw_text(f"{price['dia']}D", (card.right - 10, cy + 8), 12, d_col, align="right")
            else:
                if not is_active:
                    self.draw_text("FREE EQUIP", (card.right - 10, cy), 12, (200, 200, 255), align="right")

    def _apply_permanent_boost(self, key):
        if not self.player: return
        u = self.upgrades
        if key == "hp_boost":
            self.player.max_health += 10
            self.player.health = self.player.max_health
        elif key == "shield_boost":
            self.player.max_shield += 5
            self.player.shield = self.player.max_shield
        elif key == "speed_boost":
            self.player._speed_upg_mult = 1.0 + u.get("speed_boost", 0) * 0.03
        elif key == "xp_bonus":
            self.player._xp_upg_mult = 1.0 + u.get("xp_bonus", 0) * 0.05
        elif key == "dash_cdr":
            self.player._dash_cdr_mult = 1.0 - u.get("dash_cdr", 0) * 0.05
        elif key == "dmg_boost":
            self.player._dmg_upg_mult = 1.0 + u.get("dmg_boost", 0) * 0.10

    def _use_skill(self, idx):
        if not self.player or idx >= len(self.player.active_skills): return
        skey = self.player.active_skills[idx]
        from entities import ACTIVE_SKILLS
        skill_data = ACTIVE_SKILLS[skey]
        
        #  공명(Resonance) 시스템 판정
        if not hasattr(self, "skill_combo_list"): 
            self.skill_combo_list = []
            self.skill_combo_timer = 0
            
        if self.player.skill_cooldowns[skey] > 0:
            cd_sec = self.player.skill_cooldowns[skey] / 60
            self.notify(f" {skill_data['name']} 재사용 대기 중! ({cd_sec:.1f}s)", 60)
            return

        # 전직 통계: 스킬 사용 카운트
        self.player.job_stats["skill_uses"] += 1

        # 스킬 레벨 가져오기 (기본 1레벨)
        lvl = self.owned_skills.get(skey, 1)
            
        # 스킬별 로직 (레벨에 따른 스케일링 적용)
        if skey == "nova_blast":
            dmg = 20 + lvl * 15
            range_val = 300 + lvl * 20
            self.notify(f" 노바 블래스트! (Lv.{lvl})", 100)
            self.screen_shake(15 + lvl, 20)
            self._burst(self.player.world_pos, (255,100,0), count=60 + lvl*10, speed=12 + lvl, life=40)
            target_enemies = self.rift_enemies if self.rift_active else self.enemies
            for e in list(target_enemies):
                if (e.world_pos - self.player.world_pos).length() < range_val:
                    e.take_damage(dmg)
                    
        elif skey == "time_warp":
            duration = 120 + lvl * 60
            slow_mod = max(0.1, 0.5 - lvl * 0.08)
            self.notify(f" 타임 워프! (Lv.{lvl})", duration)
            target_enemies = self.rift_enemies if self.rift_active else self.enemies
            for e in target_enemies: 
                if hasattr(e, "speed"): e.speed *= slow_mod
                
        elif skey == "vampirism":
            dur = 600 + lvl * 300
            self.notify(f" 뱀파이어리즘 활성화 ({dur//60}초)!", 120)
            self.player.skill_vamp_timer = dur
            
        elif skey == "shield_overload":
            dmg_buff_time = 300 + lvl * 120
            self.notify(f" 쉴드 오버로드! (Lv.{lvl})", 120)
            self.player.shield = self.player.max_shield
            self.player.skill_dmg_timer = dmg_buff_time
            self._burst(self.player.world_pos, (255,255,255), count=30, speed=8, life=20)
            
        elif skey == "gravity_surge":
            from entities import Blackhole
            m_pos = pygame.mouse.get_pos()
            world_m = Vector2(m_pos) + self.camera_offset
            bh = Blackhole(world_m)
            # 블랙홀 강화
            bh.max_radius += lvl * 15
            bh.pull_range += lvl * 40
            bh.pull_force += lvl * 0.05
            bh.max_age += lvl * 600
            self.blackholes.add(bh)
            self.notify(f" {lvl}단계 중력 서지 발생!", 120)
            
        elif skey == "stealth_cloak":
            dur = 300 + lvl * 120
            self.notify(f" 스텔스 클로킹! ({dur//60}초)", 120)
            self.player.skill_stealth_timer = dur
            self.player.speed_boost = dur
            
        elif skey == "shadow_extraction":
            count = 3 + lvl // 2
            self.notify(f" 그림자 추출... {count}명의 병사 소환!", 180)
            self.screen_shake(12, 15)
            self._burst(self.player.world_pos, (100,0,255), count=40, speed=8)
            for _ in range(count):
                angle = random.uniform(0,360)
                dist = random.uniform(50, 100)
                sp = self.player.world_pos + Vector2(math.cos(math.radians(angle))*dist, math.sin(math.radians(angle))*dist)
                self.allies.add(ShadowSoldier(self.player, sp, random.choice(["hunter_drone","shadow_lurker","glitcher"])))
                
        elif skey == "getsuga_tensho":
            dmg = 25 + lvl * 25
            size = 24 + lvl * 4
            self.notify(f" 월아천충! (Lv.{lvl} Damage:{dmg})", 140)
            self.screen_shake(18, 20)
            fire_dir = self.player.get_fire_direction(self.mouse_pos)
            proj_group = self.rift_projectiles if self.rift_active else self.projectiles
            col = (0,0,0) if (not self.rift_active and self.dimension=="PHYSICAL") else (255,0,0)
            proj_group.add(Projectile(self.player.world_pos, fire_dir, "PHYSICAL" if self.rift_active else self.dimension,
                                             color_override=col, speed=12 + lvl, dmg=dmg, is_direction=True, size=size))
                                             
        elif skey == "infinite_void":
            dur = 300 + lvl * 120
            dmg = 10 + lvl * 10
            self.notify(f" 무량공처 (Lv.{lvl})", dur)
            self.freeze_timer = dur
            self.screen_shake(30, 40)
            for _ in range(5 + lvl):
                rx = random.randint(-400, 400); ry = random.randint(-300, 300)
                self._burst(self.player.world_pos + Vector2(rx, ry), (255,255,255), count=20, speed=10)
            target_enemies = self.rift_enemies if self.rift_active else self.enemies
            for e in target_enemies:
                if (e.world_pos - self.player.world_pos).length() < 1000:
                    e.take_damage(dmg)
                    
        elif skey == "titan_form":
            dur = 420 + lvl * 120
            self.notify(f" 진격의 거인! ({dur//60}초)", 240)
            self.player.skill_titan_timer = dur
            self.screen_shake(20, 30)
            self._burst(self.player.world_pos, (200, 200, 200), count=100, speed=15)
            
        elif skey == "thunder_spear":
            dmg = 60 + lvl * 40
            self.notify(f" 뇌창! (Lv.{lvl} Damage:{dmg})", 100)
            fire_dir = self.player.get_fire_direction(self.mouse_pos)
            proj_group = self.rift_projectiles if self.rift_active else self.projectiles
            p = Projectile(self.player.world_pos, fire_dir, "PHYSICAL" if self.rift_active else self.dimension,
                                             color_override=(255,180,0), speed=18, dmg=dmg, is_direction=True, size=20 + lvl*2)
            p.special = "thunder_spear" # 특별 관리
            proj_group.add(p)
                                             
        elif skey == "amaterasu":
            dmg = 100 + lvl * 150
            self.notify(f" 아마테라스! (Lv.{lvl})", 180)
            m_pos = Vector2(pygame.mouse.get_pos()) + self.camera_offset
            self._burst(m_pos, (0,0,0), count=50 + lvl*10, speed=5)
            target_enemies = self.rift_enemies if self.rift_active else self.enemies
            for e in target_enemies:
                if (e.world_pos - m_pos).length() < 150 + lvl * 20:
                    e.take_damage(dmg)

        elif skey == "hollow_purple":
            # 주술회전: 허식 자 (2단계 공격)
            self.notify(f" 허식 「자(茈)」!! (Lv.{lvl})", 180)
            self.screen_shake(25, 30)
            fire_dir = self.player.get_fire_direction(self.mouse_pos)
            # 거대 빔 형태 투사체
            target_enemies = self.rift_enemies if self.rift_active else self.enemies
            for i in range(12):
                p_pos = self.player.world_pos + fire_dir * (i * 50)
                self._burst(p_pos, (180, 0, 255), count=25, speed=12)
                for e in list(target_enemies):
                    if (e.world_pos - p_pos).length() < 120 + lvl * 15:
                        e.take_damage(300 + lvl * 150)
                        
        elif skey == "gomu_gatling":
            # 원피스: 고무고무 가틀링 (5초간 전방향 난타)
            self.notify(f" 고무고무 기간트 가틀링!!", 300)
            self.player.skill_gatling_timer = 300
            
        elif skey == "izanagi":
            # 이자나기는 패시브이므로 발동 시 쿨타임만 적용 (현재는 액티브로 눌러도 아무일 없음)
            self.notify(" 이자나기가 활성화되어 있습니다 (패시브)", 60)
            return
            
        # 스킬 사용 후 쿨타임 적용
        self.player.skill_cooldowns[skey] = skill_data["cd"]

    def _handle_menu_input(self, events):
        mx, my = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.respec_confirm_active:
                    if event.key == pygame.K_ESCAPE:
                        self.respec_confirm_active = False
                    elif event.key == pygame.K_g:
                        self._try_respec_job("gold")
                    elif event.key == pygame.K_d:
                        self._try_respec_job("diamond")
                    return
                if event.key == pygame.K_t and not self.reward_roulette_active:
                    import time
                    now = time.time()
                    wait = int(600 - (now - self.last_roulette_time))
                    if wait <= 0:
                        self.reward_roulette_active = True
                        self.reward_roulette_timer  = 0
                        self.reward_roulette_result = None
                    else:
                        self.notify(f"룰렛 충전 중... ({wait//60}분 {wait%60}초 남음)", 100)
                elif event.key == pygame.K_s:
                    self.state = "SHOP"
                    self.shop_tab = 0
                elif event.key in (pygame.K_j, pygame.K_m):
                    self.state = "SHOP"
                    self.shop_tab = 1
                    self.job_market_sel = 0
                elif event.key == pygame.K_r:
                    if getattr(self, "played_job_chapter", False) or getattr(self.player, "job", None):
                        self.respec_confirm_active = True
                    else:
                        self.notify("아직 전직을 하지 않았습니다!", 90)
                elif event.key == pygame.K_i:
                    # 메뉴에서도 스킬 관리 가능
                    if self.owned_skills:
                        self.state = "SHOP"
                        self.skill_manage_open = True
                        self.skill_manage_sel = 0
                    else:
                        self.notify("보유한 스킬이 없습니다! 상점에서 구매하세요.", 120)
                elif pygame.K_0 <= event.key <= pygame.K_9:
                    cid = str(event.key - pygame.K_0)
                    if cid in self.chapters:
                        if cid == "0" and getattr(self, "played_job_chapter", False):
                            self.respec_confirm_active = True
                        else:
                            self.start_game(cid)

            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 리워드 룰렛 버튼
                import time
                now = time.time()
                wait = int(600 - (now - self.last_roulette_time))
                
                reward_btn = pygame.Rect(310, 485, 180, 32)
                if reward_btn.collidepoint(mx, my) and not self.reward_roulette_active:
                    if wait <= 0:
                        self.reward_roulette_active = True
                        self.reward_roulette_timer = 0
                    else:
                        self.notify(f"룰렛 충전 중... ({wait//60}분 {wait%60}초 남음)", 100)
                    return


                # 챕터 시작 버튼 제거 (룰렛용)


                # 챕터 카드 직접 클릭
                chapter_list = []
                # 0번(전직)부터 챕터 ID들을 정렬하여 수집
                for cid in sorted(self.chapters.keys(), key=lambda x: int(x)):
                    chapter_list.append(cid)

                cols = 2
                card_w, card_h = 360, 75
                x_start, y_start = 35, 150
                x_gap, y_gap = 375, 80
                
                for i, cid in enumerate(chapter_list):
                    row = i // cols; ci = i % cols
                    card = pygame.Rect(x_start + ci * x_gap, y_start + row * y_gap, card_w, card_h)

                    if card.collidepoint(mx, my):
                        if cid == "0" and getattr(self, "played_job_chapter", False):
                            self.respec_confirm_active = True
                        else:
                            self.start_game(cid)
                        return

                # 상점/직업마켓 버튼 클릭 핸들링
                shop_btn = pygame.Rect(630, 560, 75, 32)
                job_btn  = pygame.Rect(715, 560, 75, 32)
                if shop_btn.collidepoint(mx, my):
                    self.state = "SHOP"
                    self.shop_tab = 0
                    return
                if job_btn.collidepoint(mx, my):
                    self.state = "SHOP"
                    self.shop_tab = 1
                    self.job_market_sel = 0
                    return

    def _apply_reward_roulette_result(self):
        pool = ["GOLD_1000", "SKILL_nova_blast", "GOLD_2000", "SKILL_time_warp", "GOLD_500", "SKILL_vampirism", "GOLD_5000", "GOLD_500"]
        res  = pool[self.reward_roulette_idx]
        from entities import ACTIVE_SKILLS
        
        if res.startswith("SKILL_"):
            skey = res.replace("SKILL_", "")
            lvl = self.owned_skills.get(skey, 0)
            if lvl >= 1:
                # 이미 보유한 스킬이면 레벨업 (최대 레벨 미만일 때)
                if lvl < ACTIVE_SKILLS.get(skey, {}).get("max_lvl", 5):
                    self.owned_skills[skey] += 1
                    sname = ACTIVE_SKILLS[skey]["name"]
                    self.reward_roulette_result = f"UPGRADE: {sname}"
                    self.notify(f"행운! {sname} 레벨업! (Lv.{self.owned_skills[skey]})", 180)
                else:
                    self.gold += 5000
                    self.reward_roulette_result = "5000G (MAX)"
                    self.notify("이미 최대 레벨! 지원금 +5000 G", 150)
            else:
                self.owned_skills[skey] = 1
                # ★ 자동 장착
                if len(self.equipped_skills) < 6:
                    self.equipped_skills.append(skey)
                sname = ACTIVE_SKILLS.get(skey, {"name": skey})["name"]
                self.reward_roulette_result = f"SKILL: {sname}"
                self.notify(f"대박! 신규 스킬 [{sname}] 획득!", 240)
        else:
            amt = int(res.split("_")[1])
            self.gold += amt
            self.reward_roulette_result = f"{amt}G"
            self.notify(f"룰렛 보상: {amt} GOLD 획득!", 150)
        
        import time
        self.last_roulette_time = time.time()
        self._save_data()

    def _handle_shop_mouse(self, event):
        from entities import PERSISTENT_UPGRADES, ACTIVE_SKILLS
        
        # 동적 리스트 재구성
        upgrades = [(k, v, False) for k, v in PERSISTENT_UPGRADES.items()]
        active_skills_list = []
        passive_skills_list = []
        for k, v in ACTIVE_SKILLS.items():
            if v.get("type") == "passive":
                passive_skills_list.append((k, v, True))
            else:
                active_skills_list.append((k, v, True))
        
        all_items = upgrades + active_skills_list + passive_skills_list
        
        if event.type == pygame.MOUSEWHEEL:
            self.shop_scroll_y += event.y * 45 # 속도 약간 증가
            if self.shop_tab == 0:
                rows = (len(all_items) + 1) // 2 + 3 
                max_scroll = -max(0, rows * 68 - 380)
            else:
                from entities import JOB_DATA
                jobs = list(JOB_DATA.keys())
                rows = (len(jobs) + 1) // 2
                max_scroll = -max(0, rows * 92 - 340)
            
            self.shop_scroll_y = min(0, max(max_scroll, self.shop_scroll_y))
            return

        mx, my = pygame.mouse.get_pos()
        cw, ch = 350, 60
        x_start, x_gap = 40, 370
        y_cursor = 190 + self.shop_scroll_y

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # ★ 스킬 관리 오버레이가 열려있으면 오버레이 클릭 처리
            if self.skill_manage_open:
                self._handle_skill_manage_click(mx, my)
                return
            
            # 헤더 영역(y < 145)은 클릭 무시
            if my < 145:
                return

            curr_idx = 0
            sections = [upgrades, active_skills_list, passive_skills_list]
            for items in sections:
                y_cursor += 35 # 섹션 타이틀 공간
                for i in range(0, len(items), 2):
                    for j in range(2):
                        if i + j >= len(items): break
                        card = pygame.Rect(x_start + j * x_gap, y_cursor, cw, ch)
                        if card.collidepoint(mx, my):
                            self.shop_sel = curr_idx
                            # 클릭하면 바로 구매 시도 (이미 선택된 상태라면)
                            fake_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
                            self._handle_shop_input(fake_event)
                            return
                        curr_idx += 1
                    y_cursor += ch + 8
                y_cursor += 15
        
            back_btn = pygame.Rect(220, 555, 160, 36)
            if back_btn.collidepoint(mx, my):
                self.state = "MENU"
                return
            
            # ★ 스킬 관리 버튼 클릭
            skill_btn = pygame.Rect(420, 555, 180, 36)
            if skill_btn.collidepoint(mx, my):
                self.skill_manage_open = True
                self.skill_manage_sel = 0
                return

    def _handle_skill_manage_click(self, mx, my):
        """스킬 관리 오버레이에서 클릭 처리"""
        from entities import ACTIVE_SKILLS
        
        # 상단 장착 슬롯 클릭 (해제)
        slot_w, slot_h = 110, 80
        gap = 8
        total_w = slot_w * 6 + gap * 5
        sx_start = (800 - total_w) // 2
        sy = 90
        
        for i in range(6):
            sx = sx_start + i * (slot_w + gap)
            slot_rect = pygame.Rect(sx, sy + 8, slot_w, slot_h - 12)
            if slot_rect.collidepoint(mx, my):
                if i < len(self.equipped_skills):
                    removed = self.equipped_skills.pop(i)
                    sname = ACTIVE_SKILLS.get(removed, {}).get("name", removed)
                    self.notify(f"스킬 해제: {sname}", 100)
                    if self.player:
                        self.player.active_skills = list(self.equipped_skills)
                    self._save_data()
                return
        
        # 하단 보유 스킬 목록 클릭 (장착/해제 토글)
        list_y = sy + slot_h + 25 + 25
        owned_list = [(k, ACTIVE_SKILLS[k]) for k in self.owned_skills if k in ACTIVE_SKILLS]
        card_w, card_h = 350, 48
        x_left, x_right = 40, 410
        
        for idx, (skey, sdata) in enumerate(owned_list):
            col_x = x_left if idx % 2 == 0 else x_right
            row_y = list_y + (idx // 2) * (card_h + 6)
            
            if row_y > 540:
                break
            
            card_rect = pygame.Rect(col_x, row_y, card_w, card_h)
            if card_rect.collidepoint(mx, my):
                if skey in self.equipped_skills:
                    self.equipped_skills.remove(skey)
                    self.notify(f"스킬 해제: {sdata['name']}", 100)
                elif len(self.equipped_skills) < 6:
                    self.equipped_skills.append(skey)
                    self.notify(f"스킬 장착: {sdata['name']}!", 100)
                else:
                    self.notify("슬롯이 꽉 찼습니다! 다른 스킬을 먼저 해제하세요.", 100)
                if self.player:
                    self.player.active_skills = list(self.equipped_skills)
                self._save_data()
                return

    # ─────────────────────────────────────
    #  DEATH REWARDS
    # ─────────────────────────────────────
    def _grant_death_rewards(self):
        from entities import ACTIVE_SKILLS
        #  이자나기 패시브 체크 (부활) — 스킬 보유 + 준비 완료 시에만 발동
        if "izanagi" in self.owned_skills and self.player.skill_izanagi_ready:
            lvl = self.owned_skills.get("izanagi", 1)
            cd = ACTIVE_SKILLS["izanagi"]["cd"]
            self.player.skill_izanagi_ready = False
            self.player.skill_cooldowns["izanagi"] = cd
            self.player.health = min(self.player.max_health, 30 + lvl * 20)
            self.notify(f" 현실은 재기록되었다... (이자나기 Lv.{lvl} 발동!)", 180)
            self.screen_shake(30, 40)
            self._burst(self.player.world_pos, (255,255,255), count=100, speed=20, life=60)
            return

        # 보상 계산 (기존보다 상향된 계수 적용)
        gold_from_score = int(self.player.score * 0.1)
        gold_from_kills = self.player.kill_count * 5
        gold_from_time  = int(self.game_time // 10)

        total_gold = gold_from_score + gold_from_kills + gold_from_time
        dia = min(100, (self.player.score // 10000) + (self.player.kill_count // 50))

        self.last_death_rewards = {
            "gold": total_gold,
            "dia":  dia,
            "score": self.player.score,
            "time":  f"{int(self.game_time//3600):02d}:{int((self.game_time%3600)//60):02d}",
            "kills": self.player.kill_count
        }
        self.gold     += total_gold
        self.diamonds += dia
        self.high_score = max(self.high_score, self.player.score)
        self.state = "DEATH"
        self._save_data()

    # ─────────────────────────────────────
    #  JOB VIEWER UI
    # ─────────────────────────────────────
    def _handle_job_viewer_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_j):
                    self.job_viewer_active = False

    def _draw_job_viewer(self):
        """사용자 상태 프로필 - 최고 기록, 장착 스킬, 직업 정보 표시"""
        from entities import ACTIVE_SKILLS, JOB_DATA, JOB_TIER_DATA
        
        # 배경 오버레이 (블러 느낌의 어두운 배경)
        ov = pygame.Surface((800, 600), pygame.SRCALPHA)
        ov.fill((10, 12, 20, 235))
        self.screen.blit(ov, (0, 0))
        
        # 메인 프레임
        frame_rect = pygame.Rect(50, 50, 700, 500)
        pygame.draw.rect(self.screen, (20, 25, 45), frame_rect, border_radius=15)
        pygame.draw.rect(self.screen, (0, 180, 255), frame_rect, 2, border_radius=15)
        
        # 제목
        self.draw_text("PLAYER STATUS PROFILE", (400, 85), 28, (0, 255, 200))
        pygame.draw.line(self.screen, (0, 150, 255), (100, 110), (700, 110), 1)

        # 1. 왼쪽 섹션: 파일럿 정보 & 최고 기록
        # ──────────────────────────────────────────
        lx = 80
        self.draw_text("ENTRY: PILOT DATA", (lx, 140), 18, (140, 180, 255), align="left")
        
        # 파일럿 정보 박스
        pygame.draw.rect(self.screen, (30, 40, 70), (lx, 160, 300, 110), border_radius=8)
        self.draw_text(f"NAME: {self.pilot_name}", (lx + 20, 185), 16, (255, 255, 255), align="left")
        self.draw_text(f"RANK: {self.pilot_rank}", (lx + 20, 210), 14, (200, 200, 200), align="left")
        self.draw_text(f"CALLSIGN: {self.pilot_callsign}", (lx + 20, 235), 14, (0, 200, 255), align="left")

        self.draw_text("RECORDS: PERSONAL BEST", (lx, 300), 18, (255, 215, 0), align="left")
        pygame.draw.rect(self.screen, (40, 35, 20), (lx, 320, 300, 140), border_radius=8)
        self.draw_text(f"HIGH SCORE: {self.high_score:,}", (lx + 20, 345), 20, (255, 230, 100), align="left")
        
        # 추가 누적 통계
        js = self.player.job_stats if self.player else getattr(self, "saved_job_stats", {})
        total_kills = js.get("melee_kills", 0) + js.get("range_kills", 0)
        self.draw_text(f"ACCUMULATED KILLS: {total_kills:,}", (lx + 20, 385), 14, (200, 200, 200), align="left")
        self.draw_text(f"MAX COMBO RECORD: {js.get('max_combo', 0)}", (lx + 20, 410), 14, (200, 200, 200), align="left")
        self.draw_text(f"DIMENSION JUMPS: {js.get('dim_switches', 0)}", (lx + 20, 435), 14, (200, 200, 200), align="left")

        # 2. 오른쪽 섹션: 현재 직업 & 장착 스킬
        # ──────────────────────────────────────────
        rx = 420
        self.draw_text("ACTIVE: JOB PROGRESSION", (rx, 140), 18, (255, 100, 100), align="left")
        
        curr_job = self.player.job if self.player else getattr(self, "saved_job", None)
        if curr_job and curr_job in JOB_DATA:
            jdata = JOB_DATA[curr_job]
            tier_idx = self.player.job_tier if self.player else 0
            tier_name = JOB_TIER_DATA["names"][tier_idx]
            tier_color = JOB_TIER_DATA["colors"][tier_idx]
            
            # 직업 카드
            pygame.draw.rect(self.screen, (45, 20, 30), (rx, 160, 330, 110), border_radius=8)
            pygame.draw.rect(self.screen, jdata["color"], (rx, 160, 330, 110), 1, border_radius=8)
            
            self.draw_text(f"CLASS: {curr_job}", (rx + 20, 185), 20, jdata["color"], align="left")
            self.draw_text(f"TIER: {tier_name}", (rx + 20, 215), 16, tier_color, align="left")
            
            # 킬 수 달성 바
            kills = self.player.job_kills if self.player else 0
            next_req = JOB_TIER_DATA["kills"][min(tier_idx + 1, 4)]
            prog = min(1.0, kills / next_req) if next_req > 0 else 1.0
            
            pygame.draw.rect(self.screen, (20, 20, 20), (rx + 20, 235, 290, 8), border_radius=4)
            pygame.draw.rect(self.screen, tier_color, (rx + 20, 235, int(290 * prog), 8), border_radius=4)
            self.draw_text(f"KILLS: {kills}/{next_req}", (rx + 20, 255), 11, (180, 180, 180), align="left")
        else:
            pygame.draw.rect(self.screen, (30, 30, 30), (rx, 160, 330, 110), border_radius=8)
            self.draw_text("NO ACTIVE JOB", (rx + 165, 215), 18, (100, 100, 100))

        # 장착 스킬 목록
        self.draw_text("EQUIPPED: TACTICAL SKILLS", (rx, 300), 18, (180, 100, 255), align="left")
        
        equipped = self.equipped_skills
        for i in range(6):
            sx = rx + (i % 2) * 170
            sy = 325 + (i // 2) * 45
            
            slot_rect = pygame.Rect(sx, sy, 160, 40)
            pygame.draw.rect(self.screen, (25, 20, 40), slot_rect, border_radius=5)
            
            if i < len(equipped):
                skey = equipped[i]
                sname = ACTIVE_SKILLS.get(skey, {}).get("name", skey)
                self.draw_text(sname, (sx + 80, sy + 20), 13, (220, 200, 255))
                pygame.draw.rect(self.screen, (150, 80, 255), slot_rect, 1, border_radius=5)
            else:
                self.draw_text("EMPTY", (sx + 80, sy + 20), 12, (60, 60, 80))

        # 푸터
        self.draw_text("[J] or [ESC] TO CLOSE PROFILE", (400, 530), 16, (100, 120, 140))

    # ─────────────────────────────────────
    def draw(self):
        shake = Vector2(0,0)
        if self.shake_timer > 0:
            shake = Vector2(random.uniform(-self.shake_amount, self.shake_amount),
                            random.uniform(-self.shake_amount, self.shake_amount))
        
        if self.state == "MENU":
            self._draw_menu()
        elif self.state == "COLOR_SELECT": self._draw_color_select()
        elif self.state == "SHOP":         self._draw_shop()
        elif self.state == "PLAYING":
            if self.rift_active:
                self._draw_rift(shake)
            else:
                self._draw_playing(shake)
        elif self.state == "DEATH":   self._draw_death()
        elif self.state == "WIN":     self._draw_win()

        # 직업 뷰어(Job Viewer) 오버레이
        if self.job_viewer_active:
            self._draw_job_viewer()
            
        # 전직 화면 오버레이 (메뉴, 게임 어디서든)
        if getattr(self, "job_select_active", False):
            self._draw_job_select_overlay()

        # 후처리 효과: 스캔라인 오퍼시티 대폭 축소 (글자 깨짐 방지)
        # self.screen.blit(self.scanline_surf, (0,0)) 
        # 대신 아주 연한 상단 레이어만 적용하거나 제거
        pass
        
        if self.settings_open:
            self._draw_settings()
            
        pygame.display.flip()

    # ─────────────────────────────────────
    def _draw_menu(self):
        self.screen.fill((6,6,12))
        rng = random.Random(42)
        for _ in range(140):
            x=rng.randint(0,800); y=rng.randint(0,600); b=rng.randint(40,160)
            pygame.draw.circle(self.screen, (b,b,b+40), (x,y), 1)

        #  아티스틱 타이틀 레이아웃 (중앙 정렬)
        title_x = 400
        for offset in range(4, 0, -1):
            self.draw_text("DIMENSION FIGHT", (title_x + offset, 58 + offset), 58, (60, 20, 10))
        
        self.draw_text("DIMENSION FIGHT", (title_x, 58), 58, (255, 245, 230))
        # 호박색(Amber) 테마로 변경
        self.draw_text("DIMENSION FIGHT", (title_x, 58), 58, (255, 150, 0))
        self.draw_text("Neon Chronicles — Paradox Survival", (title_x, 108), 24, (255, 100, 50))
        
        # 중앙 수평 구분선
        pygame.draw.line(self.screen, (100, 40, 20), (40, 135), (760, 135), 1)

        self.draw_text("PROTOCOL SELECTION PHASE", (400, 148), 12, (255, 180, 100))


        mx, my = pygame.mouse.get_pos()
        clist = []
        # 모든 챕터를 ID 순서대로 수집
        for cid in sorted(self.chapters.keys(), key=lambda x: int(x)):
            clist.append((cid, self.chapters[cid]))


        cols = 2
        card_w, card_h = 360, 75
        x_start, y_start = 35, 150
        x_gap, y_gap = 375, 80



        for i, (cid, ch) in enumerate(clist):
            row = i // cols; ci = i % cols
            card = pygame.Rect(x_start + ci * x_gap, y_start + row * y_gap, card_w, card_h)
            cx, cy = card.centerx, card.centery
            mx, my = pygame.mouse.get_pos()
            hovered = card.collidepoint(mx,my)

            # 재전직 카드 (챕터 0, 이미 완료한 경우) 특수 렌더링
            if cid == "0" and getattr(self, "played_job_chapter", False):
                pygame.draw.rect(self.screen, (20, 10, 40), card, border_radius=12)
                pygame.draw.rect(self.screen, (140, 60, 255), card, 2, border_radius=12)
                self.draw_text("재전직 (전직 재선택)", (card.centerx, card.centery - 18), 18, (200, 150, 255))
                self.draw_text("5,000,000 G  또는  1,000 D", (card.centerx, card.centery + 8), 14, (255, 220, 100))
                self.draw_text("[클릭하여 재도전]", (card.centerx, card.centery + 28), 11, (160, 120, 200))
                continue

            is_roulette_hi = self.roulette_active and (self.roulette_idx == i)
            is_result      = (self.roulette_result == cid and self.roulette_flash > 0)

            # --- 스타일 정의 (상점 테마 계승) ---
            if is_result:
                pulse   = int(40 + 40 * math.sin(self.roulette_flash * 0.25))
                bg_col  = (pulse, pulse//2, 10)
                bc      = (255, 220, 50)
                bw_line = 3
            elif is_roulette_hi:
                bg_col  = (60, 50, 20)
                bc      = (255, 180, 0)
                bw_line = 3
            elif hovered:
                bg_col = (30, 35, 60); bc = (255, 255, 120); bw_line = 2
            else:
                bg_col = (12, 14, 28)
                mode_col_base = (0, 200, 255) if ch.mode=="SHIP" else (0, 255, 150)
                bc = mode_col_base; bw_line = 1

            # 카드 배경 및 테두리
            pygame.draw.rect(self.screen, bg_col, card, border_radius=12)
            pygame.draw.rect(self.screen, bc, card, bw_line, border_radius=12)

            # --- 결과 하이라이트 이펙트 ---
            if is_result:
                for si in range(8):
                    sa = (self.game_time * 5 + si * 45) % 360
                    sr = 45 + 5 * math.sin(self.game_time * 0.1)
                    spx = cx + int(math.cos(math.radians(sa)) * sr)
                    spy = cy + int(math.sin(math.radians(sa)) * sr)
                    pygame.draw.circle(self.screen, (255,220,50), (spx,spy), 3)

            # --- 좌측 아이콘 박스 (상점 스타일) ---
            box_w = 60
            box_rect = pygame.Rect(card.left + 10, card.top + 10, box_w, card_h - 20)
            pygame.draw.rect(self.screen, (0, 0, 0, 100), box_rect, border_radius=8)
            
            mode_char = "S" if ch.mode=="SHIP" else "H"
            mode_col = (0, 200, 255) if ch.mode=="SHIP" else (0, 255, 150)
            self.draw_text(mode_char, (box_rect.centerx, box_rect.top + 18), 20, mode_col)
            self.draw_text(f"CH.{cid}", (box_rect.centerx, box_rect.top + 42), 11, (160, 160, 180))

            # --- 텍스트 정보 (우측 정렬) ---
            text_x = box_rect.right + 15
            name_col = (255,220,50) if is_result else (255, 255, 255)
            self.draw_text(ch.name, (text_x, cy - 14), 18, name_col, align="left")

            
            # 설명 (브리핑)
            ov = ch.overview[:40] + ("..." if len(ch.overview) > 40 else "")
            self.draw_text(ov, (text_x, cy + 10), 11, (140, 145, 170), align="left")
            
            # 모드 텍스트 배지
            self.draw_text(ch.mode, (card.right - 10, card.top + 15), 10, mode_col, align="right")
            
            # 위험도 (별)
            danger = i + 1
            star_str = "★" * danger
            self.draw_text(star_str, (card.right - 10, card.bottom - 15), 10, (255, 100, 50), align="right")

        # 리워드 룰렛 UI
        self._draw_reward_roulette(mx, my)

        # 하단 정보 바 (도움말 및 최고 점수)
        help_bg = pygame.Rect(50, 542, 570, 24)
        pygame.draw.rect(self.screen, (15, 15, 35), help_bg, border_radius=12)
        pygame.draw.rect(self.screen, (60, 60, 120), help_bg, 1, border_radius=12)
        self.draw_text("WASD이동 SPACE대쉬 SHIFT차원 F변형 [1~6]스킬 [S]상점 [M]마켓 [R]재전직", (335, 554), 12, (150, 160, 210))

        # 메인 메뉴 상점/직업마켓 버튼 (시각화)
        shop_btn = pygame.Rect(630, 560, 75, 32)
        job_btn  = pygame.Rect(715, 560, 75, 32)
        
        s_hov = shop_btn.collidepoint(mx, my)
        j_hov = job_btn.collidepoint(mx, my)
        
        pygame.draw.rect(self.screen, (40, 40, 80) if s_hov else (20, 20, 40), shop_btn, border_radius=8)
        pygame.draw.rect(self.screen, (255, 220, 100), shop_btn, 1, border_radius=8)
        self.draw_text("SHOP", (shop_btn.centerx, shop_btn.centery), 12, (255, 255, 255))
        
        pygame.draw.rect(self.screen, (80, 40, 40) if j_hov else (40, 20, 20), job_btn, border_radius=8)
        pygame.draw.rect(self.screen, (255, 180, 50), job_btn, 1, border_radius=8)
        self.draw_text("MARKET", (job_btn.centerx, job_btn.centery), 12, (255, 255, 255))

        if self.high_score > 0:
            self.draw_text(f"PERSONAL BEST SCORE: {self.high_score:,}", (335, 582), 16, (255, 220, 80))

        if self.respec_confirm_active:
            self._draw_respec_confirm()

    def _draw_respec_confirm(self):
        """메인 메뉴의 재전직(Respec) 확인 다이얼로그"""
        # 어두운 배경 오버레이
        ov = pygame.Surface((800, 600), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        self.screen.blit(ov, (0, 0))

        # 다이얼로그 박스
        pw, ph = 520, 280
        px, py = 400 - pw // 2, 300 - ph // 2
        
        # 외곽 광채 효과
        for i in range(3):
            pygame.draw.rect(self.screen, (100, 50, 200, 50), (px-i*2, py-i*2, pw+i*4, ph+i*4), border_radius=15+i)

        pygame.draw.rect(self.screen, (10, 10, 25), (px, py, pw, ph), border_radius=15)
        pygame.draw.rect(self.screen, (140, 80, 255), (px, py, pw, ph), 2, border_radius=15)

        # 제목 및 안내
        pulse = 0.5 + 0.5 * math.sin(self.game_time * 0.08)
        title_col = (int(200 + 55 * pulse), 180, 255)
        self.draw_text("PROTOCOL RE-SPECIFICATION", (400, py + 35), 26, title_col)
        self.draw_text("현재의 직업 프로토콜을 초기화하고 재전직하시겠습니까?", (400, py + 68), 14, (180, 180, 210))
        self.draw_text("비용을 지불하면 즉시 새로운 직업을 선택할 수 있습니다.", (400, py + 88), 13, (140, 140, 170))

        # 비용 정보
        g_can = self.gold >= self.RESPEC_GOLD_COST
        d_can = self.diamonds >= self.RESPEC_DIAMOND_COST

        # 골드 버튼
        gy = py + 120
        g_bg = (30, 45, 30) if g_can else (40, 20, 20)
        g_bd = (0, 255, 120) if g_can else (120, 50, 50)
        pygame.draw.rect(self.screen, g_bg, (px + 40, gy, pw - 80, 50), border_radius=10)
        pygame.draw.rect(self.screen, g_bd, (px + 40, gy, pw - 80, 50), 1, border_radius=10)
        self.draw_text(f"[G]  골드 결제 : {self.RESPEC_GOLD_COST:,} G", (400, gy + 25), 16, (200, 255, 200) if g_can else (255, 100, 100))

        # 다이아 버튼
        dy = gy + 65
        d_bg = (20, 35, 55) if d_can else (40, 20, 20)
        d_bd = (0, 180, 255) if d_can else (120, 50, 50)
        pygame.draw.rect(self.screen, d_bg, (px + 40, dy, pw - 80, 50), border_radius=10)
        pygame.draw.rect(self.screen, d_bd, (px + 40, dy, pw - 80, 50), 1, border_radius=10)
        self.draw_text(f"[D]  다이아 결제 : {self.RESPEC_DIAMOND_COST:,} D", (400, dy + 25), 16, (180, 230, 255) if d_can else (255, 100, 100))

        # 하단 취소 안내
        self.draw_text("[ESC] 취소하고 돌아가기", (400, py + ph - 25), 13, (120, 120, 150))


    def _draw_reward_roulette(self, mx, my):
        pool = ["1000G", "NOVA", "2000G", "TIME", "500G", "VAMP", "5000G", "500G"]
        rx, ry = 310, 485; rw, rh = 180, 32
        rect = pygame.Rect(rx, ry, rw, rh)
        hov = rect.collidepoint(mx, my)
        
        import time
        now = time.time()
        wait = int(600 - (now - self.last_roulette_time))
        
        if self.reward_roulette_active:
            bg = (60, 0, 80); tc = (255, 230, 255); bc = (230, 80, 255)
            text = f" {pool[self.reward_roulette_idx]}"
        else:
            if wait > 0:
                text = f"충전중: {wait//60:02d}:{wait%60:02d}"
                bg = (20, 20, 20); bc = (80, 80, 80); tc = (120, 120, 120)
            else:
                text = "REWARD ROULETTE [T]"
                bg = (30, 0, 40) if hov else (15, 0, 25)
                bc = (230, 80, 255) if hov else (120, 40, 180)
                tc = (255, 230, 255)
            
            if self.reward_roulette_flash > 0:
                text = f"WIN: {self.reward_roulette_result}"
                self.reward_roulette_flash -= 1

        pygame.draw.rect(self.screen, bg, rect, border_radius=8)
        pygame.draw.rect(self.screen, bc, rect, 2, border_radius=8)
        self.draw_text(text, (rx + rw//2, ry + rh//2), 14, tc)
        
        # 메뉴 클릭 이벤트 보정 (main.py에서 직접 처리하므로 여기는 draw만)

    # ─────────────────────────────────────
    def _draw_color_select(self):
        self.screen.fill((6,6,16))
        rng = random.Random(99)
        for _ in range(120):
            x=rng.randint(0,800); y=rng.randint(0,600); b=rng.randint(30,130)
            pygame.draw.circle(self.screen, (b,b,b+50), (x,y), 1)
        self.draw_text("우주선 색상 선택", (400,60), 38, (0,220,255))
        ch_name = self.chapters.get(self.pending_chapter_id, list(self.chapters.values())[0]).name
        self.draw_text(f"챕터: {ch_name}", (400,100), 20, (100,180,255))
        self.draw_text("클릭 또는 방향키로 선택  ENTER/SPACE 확정  ESC 취소", (400,130), 15, (110,110,160))

        mx, my = pygame.mouse.get_pos()
        cols = 4
        card_w, card_h = 150, 120
        x_start = 80; y_start = 240; x_gap = 165; y_gap = 140

        for i, cd in enumerate(SHIP_COLORS):
            row = i // cols; ci = i % cols
            bx = x_start + ci * x_gap; by = y_start + row * y_gap
            card = pygame.Rect(bx, by, card_w, card_h)
            sel  = (i == self.color_select_idx)
            hov  = card.collidepoint(mx, my)
            bg  = (40,30,65) if sel else ((28,28,48) if hov else (16,16,32))
            bc  = (255,230,50) if sel else ((150,150,200) if hov else (60,60,100))
            pygame.draw.rect(self.screen, bg, card, border_radius=10)
            pygame.draw.rect(self.screen, bc, card, 2 if sel else 1, border_radius=10)
            cx_c = bx + card_w // 2; cy_c = by + 52; scale = 16
            poly = [(cx_c, cy_c - scale),(cx_c + scale, cy_c + scale),(cx_c - scale, cy_c + scale)]
            col_p = cd["color_p"]; col_v = cd["color_v"]
            pygame.draw.polygon(self.screen, col_p, poly)
            pygame.draw.polygon(self.screen, (255,255,255), poly, 1)
            poly_v = [(cx_c+26, cy_c - 8),(cx_c+38, cy_c + 8),(cx_c+14, cy_c + 8)]
            pygame.draw.polygon(self.screen, col_v, poly_v)
            self.draw_text(cd["name"], (cx_c, by + card_h - 24), 15,
                           (255,230,50) if sel else (180,180,220))
            self.draw_text("P" , (cx_c - 8, by + card_h - 8), 11, col_p)
            self.draw_text("V" , (cx_c + 8, by + card_h - 8), 11, col_v)
            if sel:
                pygame.draw.rect(self.screen, (255,230,50), card, 3, border_radius=10)

        sel_cd = SHIP_COLORS[self.color_select_idx]
        preview_x, preview_y = 400, 555; big_scale = 28
        big_poly = [(preview_x, preview_y - big_scale),
                    (preview_x + big_scale, preview_y + big_scale),
                    (preview_x - big_scale, preview_y + big_scale)]
        pygame.draw.polygon(self.screen, sel_cd["color_p"], big_poly)
        pygame.draw.polygon(self.screen, (255,255,255), big_poly, 1)
        self.draw_text(f"선택: {sel_cd['name']}", (400, preview_y + big_scale + 14), 17, (255,230,80))

    # ─────────────────────────────────────
    def _draw_rift(self, shake):
        pulse = int(20 + 15 * math.sin(self.rift_timer * 0.04))
        self.screen.fill((10, 0, pulse + 8))
        cam = self.camera_offset + shake
        grid_col = (40, 0, 80); grid_spacing = 80
        offset_x = int(-cam.x % grid_spacing); offset_y = int(-cam.y % grid_spacing)
        for gx in range(-1, self.SW // grid_spacing + 2):
            lx = offset_x + gx * grid_spacing
            pygame.draw.line(self.screen, grid_col, (lx, 0), (lx, self.SH), 1)
        for gy in range(-1, self.SH // grid_spacing + 2):
            ly = offset_y + gy * grid_spacing
            pygame.draw.line(self.screen, grid_col, (0, ly), (self.SW, ly), 1)

        pcx = int(0 - cam.x); pcy = int(-200 - cam.y)
        for ri, (r, alpha, col) in enumerate([
            (80, 40, (100, 0, 200)), (55, 80, (160, 0, 255)), (30, 150, (220, 100, 255)),
        ]):
            try:
                s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(s, (*col, alpha), (r+2, r+2), r, 4)
                self.screen.blit(s, (pcx-r-2, pcy-r-2))
            except Exception:
                pass

        rng2 = random.Random(77)
        for _ in range(80):
            sx = rng2.randint(0,800); sy = rng2.randint(0,600); b  = rng2.randint(40,130)
            pygame.draw.circle(self.screen, (b//2, 0, b), (sx, sy), 1)

        for enemy in self.rift_enemies:
            enemy.update_screen_pos(cam)
            bx = enemy.rect.left; by_e = enemy.rect.top-8; bw = enemy.rect.width
            if enemy.max_hp >= 3:
                pygame.draw.rect(self.screen, (60,0,0), (bx, by_e, bw, 5))
                fill = int(bw * enemy.hp / enemy.max_hp)
                pygame.draw.rect(self.screen, (200,50,255), (bx, by_e, fill, 5))
                if enemy.max_hp >= 20:
                    f = self._get_font(13)
                    t = f.render(enemy.name, True, (255,180,255))
                    self.screen.blit(t, (bx, by_e - 14))
            self.screen.blit(enemy.image, enemy.rect)

        for p in self.rift_projectiles:
            p.update_screen_pos(cam)
            self.screen.blit(p.image, p.rect)
        for ep in self.rift_ep:
            ep.update_screen_pos(cam)
            self.screen.blit(ep.image, ep.rect)

        for ally in self.allies:
            ally.update_screen_pos(cam)
            self.screen.blit(ally.image, ally.rect)

        self.screen.blit(self.player.image, self.player.rect)

        for particle in self.rift_particles:
            particle.draw(self.screen, cam)

        mx, my = self.mouse_pos
        pygame.draw.circle(self.screen, (200,80,255), (mx,my), 7, 1)
        pygame.draw.line(self.screen, (200,80,255), (mx-12,my),(mx+12,my), 1)
        pygame.draw.line(self.screen, (200,80,255), (mx,my-12),(mx,my+12), 1)

        self._draw_rift_hud()

        if self.bh_flash_timer > 0:
            alpha = int(255 * self.bh_flash_timer / 40)
            try:
                ov = pygame.Surface((800,600), pygame.SRCALPHA)
                ov.fill((180, 0, 255, alpha))
                self.screen.blit(ov, (0,0))
            except Exception:
                pass

        if self.notify_timer > 0:
            self.draw_text(self.notify_text, (400,568), 20, (255,200,255))

    def _draw_rift_hud(self):
        hp_ratio = max(0, self.player.health/self.player.max_health)
        hw = 170
        pygame.draw.rect(self.screen,(50,8,8),(10,26,hw,15),border_radius=4)
        hpc = (80,255,80) if hp_ratio>0.6 else ((255,200,0) if hp_ratio>0.3 else (255,50,50))
        pygame.draw.rect(self.screen,hpc,(10,26,int(hw*hp_ratio),15),border_radius=4)
        pygame.draw.rect(self.screen,(100,100,130),(10,26,hw,15),1,border_radius=4)
        self.draw_text(f"HP {self.player.health}/{self.player.max_health}",(10+hw//2,33),14)

        if self.rift_boss and self.rift_boss.alive():
            bw = 400
            bh_ratio = max(0, self.rift_boss.hp / self.rift_boss.max_hp)
            pygame.draw.rect(self.screen,(40,0,60),(200,8,bw,18),border_radius=6)
            fill = int(bw * bh_ratio)
            pcol = (220,50,255) if bh_ratio > 0.5 else (255,80,80)
            pygame.draw.rect(self.screen, pcol,(200,8,fill,18),border_radius=6)
            pygame.draw.rect(self.screen,(180,0,255),(200,8,bw,18),2,border_radius=6)
            k = self.rift_boss_kill_count
            scale_txt = f"  [×{1.0+k*0.35:.1f}]" if k > 0 else ""
            self.draw_text(
                f"{self.rift_boss.name}  {self.rift_boss.hp}/{self.rift_boss.max_hp}{scale_txt}",
                (400,17),15,(255,180,255))

        self.draw_text(" 제3차원 ", (660,18), 17, (200,80,255))
        kill_col = (255,150,255) if self.rift_boss_kill_count > 0 else (150,80,180)
        self.draw_text(f"처치:{self.rift_boss_kill_count}회", (660,38), 14, kill_col)
        self.draw_text(f"점수: {self.player.score:,}", (660,56), 14, (255,220,80))
        self.draw_text("보스 처치 시 탈출!", (400,580), 16, (200,100,255))

    # ─────────────────────────────────────
    def _draw_playing(self, shake):
        progress  = min(1.0, self.game_time / (self.current_chapter.duration * 60))
        bg        = self.current_chapter.get_bg(progress,
                                                 void=(self.dimension=="VOID"),
                                                 abyss=self.abyss_active)

        #  잠수 중 배경 어두워짐
        if self.player.dive_active:
            d = self.player.dive_depth / self.player.dive_max
            bg = tuple(max(0, int(c * (1 - d * 0.7))) for c in bg)

        self.screen.fill(bg)
        
        # ★ 실존 우주 이론: 열적 죽음 시각화 (Entropy Darkening)
        if self.entropy > 0.05:
            # 엔트로피가 높아질수록 우주가 어두워짐 (열적 죽음 테마)
            dark_alpha = int(self.entropy * 160)
            try:
                overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
                overlay.fill((0, 0, 5, dark_alpha))
                self.screen.blit(overlay, (0, 0))
            except: pass
        
        #  멀티버스 시선 효과 적용 전 단계
        if self.universe_type == "ABYSSAL":
            # 심연 차원: 시야 제한 마스크 준비 (나중에 덮음)
            pass
        elif self.universe_type == "GLITCH":
            # 글리치 분열: 카메라 강제 흔들림 효과 추가
            shake.x += random.uniform(-4, 4)
            shake.y += random.uniform(-4, 4)
        self.star_field.draw(self.screen, self.camera_offset,
                              self.dimension, abyss=self.abyss_active)

        if self.abyss_active:
            pulse = int(30 + 20 * math.sin(self.game_time * 0.05))
            try:
                ov = pygame.Surface((800,600), pygame.SRCALPHA)
                ov.fill((0, pulse, pulse*2, 18))
                self.screen.blit(ov, (0,0))
            except Exception:
                pass

        #  잠수 중 압력 파동 이펙트
        if self.player.dive_active and self.player.dive_depth > 20:
            d_ratio = self.player.dive_depth / self.player.dive_max
            wave_r = int(40 + 80 * ((self.game_time % 60) / 60))
            wave_alpha = int(80 * d_ratio * (1 - (self.game_time % 60) / 60))
            try:
                ws = pygame.Surface((wave_r*2+4, wave_r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(ws, (0, 180, 255, wave_alpha), (wave_r+2, wave_r+2), wave_r, 2)
                self.screen.blit(ws, (400-wave_r-2, 300-wave_r-2))
            except Exception:
                pass
            # 잠수 깊이 비네트
            try:
                vw = pygame.Surface((800,600), pygame.SRCALPHA)
                edge_alpha = int(d_ratio * 100)
                vw.fill((0, 0, int(80*d_ratio), edge_alpha))
                self.screen.blit(vw, (0,0))
            except Exception:
                pass

        #  연속킬 streak 화면 플래시
        if self.streak_flash_timer > 0:
            t = self.streak_flash_timer / 45
            try:
                sf = pygame.Surface((800,600), pygame.SRCALPHA)
                sf.fill((255, 200, 0, int(t * 60)))
                self.screen.blit(sf, (0,0))
            except Exception:
                pass

        #  과부하 화면 오버레이
        if self.player.overload_timer > 0:
            ol_t = self.player.overload_timer / 300
            pulse2 = int(20 * abs(math.sin(self.game_time * 0.2)))
            try:
                ov2 = pygame.Surface((800,600), pygame.SRCALPHA)
                ov2.fill((255, 80, 0, int(ol_t * 30 + pulse2)))
                self.screen.blit(ov2, (0,0))
            except Exception:
                pass

        if self.bh_suck_timer > 0:
            t = self.bh_suck_timer / 60.0
            try:
                vignette = pygame.Surface((800,600), pygame.SRCALPHA)
                vignette.fill((0,0,0,0))
                edge_alpha = int((1-t) * 220)
                pygame.draw.rect(vignette, (0,0,0,edge_alpha), (0,0,800,600))
                hole_r = int(t * 320)
                pygame.draw.circle(vignette, (0,0,0,0), (400,300), hole_r)
                self.screen.blit(vignette, (0,0))
            except Exception:
                pass
            bh = self.bh_suck_target
            if bh:
                bcx = int(bh.world_pos.x - self.camera_offset.x)
                bcy = int(bh.world_pos.y - self.camera_offset.y)
                spin = (1 - t)
                for ri in range(6):
                    r = int(30 + ri * 40 * t + spin * ri * 20)
                    alpha = int(180 * (1-t) * (1 - ri/6))
                    angle_off = self.game_time * (4 + ri * 2)
                    try:
                        s = pygame.Surface((r*2+4,r*2+4), pygame.SRCALPHA)
                        col_r = min(255, 100 + ri*30)
                        pygame.draw.arc(s, (col_r, 0, 255, alpha),
                                        (2,2,r*2,r*2),
                                        math.radians(angle_off % 360),
                                        math.radians((angle_off+270) % 360), 3)
                        self.screen.blit(s, (bcx-r-2, bcy-r-2))
                    except Exception:
                        pass
            alpha_t = int((1-t) * 255)
            msg_surf = self._get_font(26).render("블랙홀에 흡입됨...", True, (200, 80, 255))
            msg_surf.set_alpha(alpha_t)
            self.screen.blit(msg_surf, msg_surf.get_rect(center=(400, 300)))

        if self.bh_flash_timer > 0:
            alpha = int(255 * self.bh_flash_timer / 40)
            try:
                ov = pygame.Surface((800,600), pygame.SRCALPHA)
                ov.fill((160, 0, 255, alpha))
                self.screen.blit(ov, (0,0))
            except Exception:
                pass

        cam = self.camera_offset + shake

        for sg in [self.fluids, self.structures]:
            for spr in sg:
                spr.update_screen_pos(cam)
                self.screen.blit(spr.image, spr.rect)

        for item in self.items:
            item.update_screen_pos(cam)
            if item.age > 480 and (item.age//8)%2==0: continue
            self.screen.blit(item.image, item.rect)

        for gem in self.gems:
            gem.update_screen_pos(cam)
            self.screen.blit(gem.image, gem.rect)

        for bh in self.blackholes:
            bh.draw(self.screen, cam, self.game_time)

        # ★ 포탈 그리기
        for portal in self.portals:
            portal.draw(self.screen, cam, self.game_time)
            
        # ★ 포탈 흡입 애니메이션 효과
        if self.portal_suck_timer > 0 and self.portal_suck_target:
            t = 1.0 - (self.portal_suck_timer / 120.0)
            try:
                # 1. 화면 색상 오버레이 (점점 진해짐)
                ov = pygame.Surface((800, 600), pygame.SRCALPHA)
                target_u = self.portal_suck_target.target_universe
                col = self.universes.get(target_u, {"color": (255,255,255)})["color"]
                ov.fill((*col, int(t * 180)))
                self.screen.blit(ov, (0, 0))
                
                # 2. 중심부로 빨려 들어가는 에너지 선
                for i in range(24):
                    angle = math.radians(i * 15 + self.game_time * 10)
                    r_outer = 1200 * (1 - t)
                    px = 400 + math.cos(angle) * r_outer
                    py = 300 + math.sin(angle) * r_outer
                    pygame.draw.line(self.screen, (255, 255, 255, int((1-t)*255)), (400, 300), (px, py), 2)
                
                # 3. 텍스트 효과
                msg = self._get_font(32).render("MULTI-DIMENSIONAL JUMP...", True, (255, 255, 255))
                msg.set_alpha(int(t * 255))
                self.screen.blit(msg, msg.get_rect(center=(400, 300 + int((1-t)*100))))
            except: pass

        for enemy in self.enemies:
            enemy.update_screen_pos(cam)
            show = enemy.dimension_type == self.dimension or self.abyss_active
            if show:
                if enemy.max_hp >= 3:
                    bx = enemy.rect.left; by = enemy.rect.top-8; bw = enemy.rect.width
                    pygame.draw.rect(self.screen, (60,0,0), (bx,by,bw,5))
                    fill = int(bw*enemy.hp/enemy.max_hp)
                    hpc  = (255,180,0) if enemy.max_hp>=20 else (255,60,60)
                    pygame.draw.rect(self.screen, hpc, (bx,by,fill,5))
                    if enemy.max_hp >= 20:
                        f = self._get_font(13); t = f.render(enemy.name, True, (255,230,100))
                        self.screen.blit(t, (bx, by-14))
                self.screen.blit(enemy.image, enemy.rect)
                
                #  피격 플래시 효과
                if enemy.flash_timer > 0:
                    enemy.flash_timer -= 1
                    flash_surf = pygame.Surface(enemy.image.get_size(), pygame.SRCALPHA)
                    flash_surf.fill((255, 255, 255, 180)) # 반투명 흰색
                    self.screen.blit(flash_surf, enemy.rect, special_flags=pygame.BLEND_RGBA_ADD)

        for p in self.projectiles:
            p.update_screen_pos(cam)
            #  탄환 잔상 효과 (속도감)
            prev_x = int(p.world_pos.x - p.vel.x - cam.x)
            prev_y = int(p.world_pos.y - p.vel.y - cam.y)
            pygame.draw.line(self.screen, (255, 255, 255, 80), (prev_x, prev_y), p.rect.center, 2)
            self.screen.blit(p.image, p.rect)

        for ep in self.enemy_projectiles:
            ep.update_screen_pos(cam)
            if ep.dimension == self.dimension or self.abyss_active:
                self.screen.blit(ep.image, ep.rect)

        for comp in self.companions:
            self.screen.blit(comp.image, comp.rect)

        for ally in self.allies:
            self.screen.blit(ally.image, ally.rect)

        self.screen.blit(self.player.image, self.player.rect)

        for particle in self.particles:
            particle.draw(self.screen, cam)

        mx,my = self.mouse_pos
        col_c = (0,220,255) if self.abyss_active else (255,255,100)
        if self.player.overload_timer > 0: col_c = (255,120,0)
        pygame.draw.circle(self.screen, col_c, (mx,my), 7, 1)
        pygame.draw.line(self.screen, col_c, (mx-12,my),(mx+12,my), 1)
        pygame.draw.line(self.screen, col_c, (mx,my-12),(mx,my+12), 1)

        self._draw_hud(progress)
        self._draw_minimap()

        if self.abyss_active:
            self._draw_abyss_bar()

        #  심해 잠수 UI (diving 챕터 전용)
        if "diving" in self.current_chapter.special:
            self._draw_dive_ui()

        if getattr(self, "form_select_active", False):
            self._draw_form_select()
        elif getattr(self, "levelup_active", False):
            self._draw_levelup_overlay()

        if self.notify_timer > 0:
            alpha = min(255, self.notify_timer*4)
            try:
                surf = pygame.Surface((640,34), pygame.SRCALPHA)
                surf.fill((0,0,0,int(110*alpha/255)))
                self.screen.blit(surf,(80,552))
            except Exception:
                pass
            self.draw_text(self.notify_text, (400,568), 20, (255,240,100))

        if self.player.combo >= 3:
            mult = self.player.get_combo_multiplier()
            c = int(min(255, 80+self.player.combo*7))
            self.draw_text(f"COMBO ×{self.player.combo}  ×{mult:.1f}", (660,80), 22, (255,c,50))

        #  과부하 타이머 표시
        if self.player.overload_timer > 0:
            ot = self.player.overload_timer
            self.draw_text(f" OVERLOAD {ot//60}.{(ot%60)//6}s", (400, 80), 24, (255,150,0))
            
        #  멀티버스 상태 표시 (스킬 바 오른쪽)
        u_data = self.universes[self.universe_type]
        self.draw_text(f" {u_data['name']}", (88, 73), 18, u_data["color"], align="left")
        self.draw_text(f"MOD: {u_data['buff']}", (88, 93), 13, (180, 180, 220), align="left")

        # ★ 엔트로피(우주 수명) UI
        e_color = (int(100 + 155 * self.entropy), 120, int(255 - 155 * self.entropy))
        self.draw_text(f"ENTROPY: {self.entropy*100:.1f}%", (88, 110), 14, e_color, align="left")

        # ── 멀티버스 시각 오버레이 (은은하게 — 게임플레이 방해 최소화) ──
        if self.universe_type == "CYBER":
            # 8프레임마다 한 번 가는 스캔라인 (매 프레임 X)
            if self.game_time % 8 < 2:
                try:
                    ct = pygame.Surface((800,600), pygame.SRCALPHA)
                    ct.fill((255, 255, 0, 4))
                    self.screen.blit(ct, (0,0))
                except: pass
        elif self.universe_type == "GOLDEN":
            try:
                gt = pygame.Surface((800,600), pygame.SRCALPHA)
                gt.fill((255, 200, 0, 6))
                self.screen.blit(gt, (0,0), special_flags=pygame.BLEND_RGB_ADD)
            except: pass
        elif self.universe_type == "ABYSSAL":
            # 약한 비네트 (시야를 많이 막지 않음)
            try:
                mask = pygame.Surface((800,600), pygame.SRCALPHA)
                mask.fill((0, 0, 0, 90))
                pygame.draw.circle(mask, (0,0,0,0), (400,300), 310)
                self.screen.blit(mask, (0,0))
            except: pass
        elif self.universe_type == "GLITCH" and (self.game_time % 40 < 3):
            # 가끔 짧게만 화면 흔들림
            shift_x = random.randint(-4, 4)
            try:
                snap = self.screen.copy()
                self.screen.blit(snap, (shift_x, 0))
            except: pass

    # ─────────────────────────────────────
    def _draw_dive_ui(self):
        """심해 잠수 깊이 + 산소 UI — 화면 좌측"""
        # 잠수 깊이 바 (세로)
        bx, by, bw, bh = 795, 30, 10, 180
        pygame.draw.rect(self.screen, (0,20,60), (bx, by, bw, bh), border_radius=4)
        depth_ratio = self.player.dive_depth / self.player.dive_max
        fill_h = int(bh * depth_ratio)
        depth_col = (0, int(80*(1-depth_ratio)+40), int(180+75*depth_ratio))
        pygame.draw.rect(self.screen, depth_col, (bx, by + bh - fill_h, bw, fill_h), border_radius=4)
        pygame.draw.rect(self.screen, (0,150,255), (bx, by, bw, bh), 1, border_radius=4)

        if self.player.dive_active:
            d_pct = int(depth_ratio * 100)
            self.draw_text(f"↓{d_pct}%", (bx + bw//2 + 14, by + bh//2), 12, depth_col)

        # 산소 바 (가로, 화면 하단)
        ox, oy, ow, oh = 10, 575, 200, 8
        pygame.draw.rect(self.screen, (0,20,50), (ox, oy, ow, oh), border_radius=4)
        o_ratio = self.player.dive_oxygen / self.player.dive_max_oxygen
        o_fill = int(ow * o_ratio)
        o_col = (0, 200, 255) if o_ratio > 0.5 else ((255, 200, 0) if o_ratio > 0.25 else (255, 50, 50))
        if o_ratio < 0.25 and (self.game_time // 8) % 2 == 0:
            o_col = (255, 255, 255)   # 위험 깜빡임
        pygame.draw.rect(self.screen, o_col, (ox, oy, o_fill, oh), border_radius=4)
        pygame.draw.rect(self.screen, (0,100,200), (ox, oy, ow, oh), 1, border_radius=4)

        o_sec = self.player.dive_oxygen // 60
        oxy_col = (0,200,255) if o_ratio > 0.5 else ((255,200,0) if o_ratio > 0.25 else (255,80,80))
        self.draw_text(f"O₂ {o_sec}s", (ox + ow//2, oy + oh + 10), 14, oxy_col)

        # 안내
        if not self.player.dive_active:
            self.draw_text("[Z] 심해 잠수", (110, oy - 12), 13, (0,150,200))

    def _draw_abyss_bar(self):
        remain = self.abyss_timer / self.ABYSS_DURATION
        pulse  = int(200 + 55*math.sin(self.game_time*0.1))
        pygame.draw.rect(self.screen, (0,30,60), (10,595,780,4))
        pygame.draw.rect(self.screen, (0,pulse,255), (10,595,int(780*remain),4))
        sec = self.abyss_timer // 60
        self.draw_text(f"심해 차원 {sec}s", (400,590), 15, (0,200,255))

    def _draw_shop(self):
        self.screen.fill((8, 6, 16))
        rng = random.Random(13)
        for _ in range(80):
            x=rng.randint(0,800); y=rng.randint(0,600); b=rng.randint(10,50)
            pygame.draw.circle(self.screen, (b+40, b, b+80), (x,y), 1)

        self.draw_text("NEON NEXUS MARKET", (400, 45), 44, (255, 220, 100))
        self.draw_text("Protocol Enhancement & Skill Acquisition", (400, 85), 18, (255, 120, 50))
        
        # 보유 자원 바
        pygame.draw.rect(self.screen, (50, 35, 20), (100, 105, 600, 35), border_radius=10)
        self.draw_text(f"CREDITS: {self.gold:,} G   |   DIAMONDS: {self.diamonds:,} D", (400, 122), 18, (255, 230, 80))

        # --- 탭 UI 추가 ---
        tab_bg = pygame.Rect(100, 145, 600, 30)
        pygame.draw.rect(self.screen, (20, 20, 30), tab_bg, border_radius=8)
        
        tab_upg_rect = pygame.Rect(100, 145, 300, 30)
        tab_job_rect = pygame.Rect(400, 145, 300, 30)
        
        if self.shop_tab == 0:
            pygame.draw.rect(self.screen, (0, 150, 255), tab_upg_rect, border_radius=8)
            self.draw_text("CORE UPGRADES & SKILLS", (250, 160), 14, (255, 255, 255))
            self.draw_text("JOB MARKET [M]", (550, 160), 14, (100, 100, 150))
        else:
            pygame.draw.rect(self.screen, (255, 180, 50), tab_job_rect, border_radius=8)
            self.draw_text("CORE UPGRADES & SKILLS [S]", (250, 160), 14, (100, 100, 150))
            self.draw_text("JOB MARKET", (550, 160), 14, (255, 255, 255))
        # ------------------

        if self.shop_tab == 1:
            self._draw_job_market()
            # 하단 버튼
            back_btn = pygame.Rect(320, 555, 160, 36)
            mx, my = pygame.mouse.get_pos()
            back_hov = back_btn.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (40, 45, 75) if back_hov else (20, 25, 40), back_btn, border_radius=10)
            pygame.draw.rect(self.screen, (100, 120, 255), back_btn, 1, border_radius=10)
            self.draw_text("RETURN [ESC]", (400, 573), 14, (220, 230, 255))
            self.screen.set_clip(None) # 클리핑 해제 필수
            return

        from entities import PERSISTENT_UPGRADES, ACTIVE_SKILLS
        
        # 섹션 분류
        upgrades = [(k, v, False) for k, v in PERSISTENT_UPGRADES.items()]
        active_skills = []
        passive_skills = []
        for k, v in ACTIVE_SKILLS.items():
            if v.get("type") == "passive":
                passive_skills.append((k, v, True))
            else:
                active_skills.append((k, v, True))
        
        #  섹션 아이콘 & 색상 정의 (액티브/패시브 시각적 분리 강화)
        section_styles = {
            "PERMANENT UPGRADES":   {"icon": "", "color": (255, 200, 80),  "line_col": (120, 80, 0),  "bg_tint": (30, 25, 10)},
            "ACTIVE COMBAT SKILLS": {"icon": "", "color": (255, 80, 100),  "line_col": (150, 30, 50), "bg_tint": (35, 10, 15)},
            "PASSIVE ABILITIES":    {"icon": "", "color": (80, 255, 180), "line_col": (0, 100, 60),  "bg_tint": (10, 30, 20)},
        }
        
        sections = [
            ("PERMANENT UPGRADES", upgrades),
            ("ACTIVE COMBAT SKILLS", active_skills),
            ("PASSIVE ABILITIES", passive_skills)
        ]
        
        mx, my = pygame.mouse.get_pos()
        cw, ch = 350, 60
        x_start, x_gap = 40, 370
        y_cursor = 190 + self.shop_scroll_y
        
        # 클리핑 설정 (헤더 및 탭 영역 보호 - 180부터 시작)
        self.screen.set_clip(pygame.Rect(0, 180, 800, 600 - 180))
        
        curr_idx = 0
        hovered_item = None

        for sec_name, items in sections:
            style = section_styles[sec_name]
            #  강화된 섹션 타이틀 — 아이콘 + 컬러 라인 + 배경 띠
            if y_cursor > 100 and y_cursor < 600:
                # 섹션 배경 띠
                sec_bg = pygame.Rect(x_start - 5, y_cursor, 730, 30)
                pygame.draw.rect(self.screen, style["bg_tint"], sec_bg, border_radius=6)
                # 컬러 라인 (좌우)
                pygame.draw.line(self.screen, style["line_col"], (x_start, y_cursor + 15), (x_start + 50, y_cursor + 15), 2)
                pygame.draw.line(self.screen, style["line_col"], (760 - 50, y_cursor + 15), (760, y_cursor + 15), 2)
                # 아이콘 + 타이틀
                title_text = f"{style['icon']}  {sec_name}  ({len(items)})"
                self.draw_text(title_text, (400, y_cursor + 15), 17, style["color"])
            y_cursor += 35
            
            for i in range(0, len(items), 2):
                for j in range(2):
                    if i + j >= len(items): break
                    ukey, data, is_skill = items[i+j]
                    
                    lvl = self.upgrades.get(ukey, 0) if not is_skill else self.owned_skills.get(ukey, 0)
                    card = pygame.Rect(x_start + j * x_gap, y_cursor, cw, ch)
                    sel = (self.shop_sel == curr_idx); hov = card.collidepoint(mx, my)
                    
                    if hov and my > 145:
                        hovered_item = (ukey, data, is_skill, lvl)
                    
                    #  카드 배경색 — 섹션별 틴트 적용
                    if not is_skill:
                        bg = (50, 40, 15) if sel else ((30, 25, 8) if hov else (18, 15, 6))
                        bc = (255, 200, 60) if sel else ((160, 120, 40) if hov else (70, 55, 25))
                    elif data.get("type") == "passive":
                        bg = (15, 50, 35) if sel else ((10, 35, 22) if hov else (6, 20, 14))
                        bc = (0, 255, 150) if sel else ((0, 180, 110) if hov else (0, 80, 50))
                    else:
                        bg = (50, 15, 25) if sel else ((35, 10, 18) if hov else (22, 8, 12))
                        bc = (255, 80, 120) if sel else ((200, 50, 80) if hov else (100, 25, 45))

                    pygame.draw.rect(self.screen, bg, card, border_radius=10)
                    pygame.draw.rect(self.screen, bc, card, 2 if sel else 1, border_radius=10)

                    icon_rect = pygame.Rect(card.left+8, card.top+8, 44, 44)
                    pygame.draw.rect(self.screen, (0,0,0,100), icon_rect, border_radius=5)
                    if is_skill and data.get("type") == "passive":
                        self.draw_text("P", (card.left+30, card.top+20), 14, (0, 255, 150))
                    elif is_skill:
                        self.draw_text("A", (card.left+30, card.top+20), 14, (255, 80, 100))
                    else:
                        self.draw_text("U", (card.left+30, card.top+20), 14, (255, 200, 60))
                    self.draw_text(f"LV.{lvl}", (card.left+30, card.top+38), 11, bc)
                    
                    # ★ 장착 상태 배지 (스킬만)
                    if is_skill and lvl > 0:
                        is_equipped = ukey in self.equipped_skills
                        if is_equipped:
                            eq_col = (0, 255, 120)
                            pygame.draw.rect(self.screen, (0, 40, 20), (card.left+8, card.top+2, 44, 12), border_radius=3)
                            self.draw_text("★장착", (card.left+30, card.top+8), 9, eq_col)
                        else:
                            eq_col = (120, 120, 140)
                            pygame.draw.rect(self.screen, (20, 20, 30), (card.left+8, card.top+2, 44, 12), border_radius=3)
                            self.draw_text("☆미장착", (card.left+30, card.top+8), 9, eq_col)

                    # 이름 + 간단 설명
                    self.draw_text(data["name"], (card.left + 60, card.top + 16), 15, (240, 240, 220), align="left")
                    desc_short = data["desc"][:28] + "..." if len(data["desc"]) > 28 else data["desc"]
                    self.draw_text(desc_short, (card.left + 60, card.top + 35), 10, (140, 140, 160), align="left")
                    
                    # 가격
                    base_cost = data["cost"]
                    current_cost = base_cost * (lvl + 1) if lvl < data["max_lvl"] else -1
                    if current_cost > 0:
                        currency = data.get("currency", "gold")
                        cur_icon = "G" if currency=="gold" else "D"
                        has_enough = (currency == "gold" and self.gold >= current_cost) or (currency == "diamond" and self.diamonds >= current_cost)
                        c_col = (255, 230, 80) if has_enough else (255, 80, 80)
                        self.draw_text(f"{current_cost}{cur_icon}", (card.right - 15, card.top + 22), 14, c_col, align="right")
                        if sel:
                            self.draw_text("CLICK/SPACE", (card.right - 15, card.top + 40), 9, (180, 180, 180), align="right")
                    else:
                        self.draw_text("MAX", (card.right - 15, card.top + 22), 14, (0, 255, 150), align="right")
                        self.draw_text(f"Lv.{data['max_lvl']}", (card.right - 15, card.top + 40), 10, (100, 200, 150), align="right")

                    curr_idx += 1
                y_cursor += ch + 8
            y_cursor += 20
            
        self.screen.set_clip(None)

        #  마우스 호버 시 상세 툴팁 표시
        if hovered_item:
            ukey, data, is_skill, lvl = hovered_item
            self._draw_shop_tooltip(mx, my, ukey, data, is_skill, lvl)

        back_btn = pygame.Rect(220, 555, 160, 36); back_hov = back_btn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (40, 45, 75) if back_hov else (20, 25, 40), back_btn, border_radius=10)
        pygame.draw.rect(self.screen, (100, 120, 255), back_btn, 1, border_radius=10)
        self.draw_text("RETURN [ESC]", (300, 573), 14, (200, 220, 255))
        
        # 스킬 관리 버튼
        skill_btn = pygame.Rect(420, 555, 180, 36); skill_hov = skill_btn.collidepoint(mx, my)
        eq_count = len(self.equipped_skills)
        btn_col = (40, 55, 45) if skill_hov else (20, 35, 25)
        pygame.draw.rect(self.screen, btn_col, skill_btn, border_radius=10)
        pygame.draw.rect(self.screen, (0, 220, 150), skill_btn, 1, border_radius=10)
        self.draw_text(f"SKILLS [{eq_count}/6] [I]", (510, 573), 14, (0, 255, 180))
        
        # ★ 키 안내 (SPACE/ENTER 구매, E 장착토글)
        self.draw_text("SPACE:구매  E:장착/해제  I:스킬관리", (400, 543), 11, (100, 120, 160))
        
        # ★ 스킬 관리 오버레이 그리기
        if self.skill_manage_open:
            self._draw_skill_manage_overlay()

    def _draw_shop_tooltip(self, mx, my, ukey, data, is_skill, lvl):
        """ 마우스 호버 시 스킬/업그레이드의 상세 혜택을 표시하는 툴팁"""
        tw, th = 320, 200
        tx = mx + 20 if mx < 430 else mx - tw - 20
        ty = my + 20 if my < 380 else my - th - 20
        # 화면 밖으로 나가지 않도록 클램핑
        tx = max(5, min(795 - tw, tx))
        ty = max(5, min(595 - th, ty))
        
        t_rect = pygame.Rect(tx, ty, tw, th)
        # 배경 (반투명 다크)
        try:
            bg_surf = pygame.Surface((tw, th), pygame.SRCALPHA)
            bg_surf.fill((8, 8, 20, 235))
            self.screen.blit(bg_surf, (tx, ty))
        except:
            pygame.draw.rect(self.screen, (8, 8, 20), t_rect, border_radius=12)
        # 테두리 색 (타입에 따라 다름)
        if is_skill and data.get("type") == "passive":
            border_col = (0, 255, 150)
            title_col  = (80, 255, 180)
            type_label = "[패시브 스킬]"
        elif is_skill:
            border_col = (255, 80, 120)
            title_col  = (255, 120, 150)
            type_label = "[액티브 스킬]"
        else:
            border_col = (255, 200, 60)
            title_col  = (255, 220, 100)
            type_label = "[영구 업그레이드]"
        pygame.draw.rect(self.screen, border_col, t_rect, 2, border_radius=12)
        
        # ── 제목 + 타입
        self.draw_text(f"「{data['name']}」", (tx + 15, ty + 18), 17, title_col, align="left")
        self.draw_text(type_label, (tx + tw - 15, ty + 18), 11, border_col, align="right")
        
        # ── 기본 설명 (줄 바꿈 처리)
        desc = data["desc"]
        if len(desc) > 34:
            self.draw_text(desc[:34], (tx + 15, ty + 42), 12, (200, 200, 220), align="left")
            self.draw_text(desc[34:68], (tx + 15, ty + 58), 12, (200, 200, 220), align="left")
        else:
            self.draw_text(desc, (tx + 15, ty + 42), 12, (200, 200, 220), align="left")
        
        # ── 구분선
        pygame.draw.line(self.screen, (60, 60, 80), (tx + 10, ty + 72), (tx + tw - 10, ty + 72), 1)
        
        # ── 현재 레벨 효과 (Current)
        cur_txt = self._get_skill_effect_text(ukey, data, is_skill, lvl)
        self.draw_text(f" 현재 Lv.{lvl}: {cur_txt}", (tx + 15, ty + 88), 12, (180, 220, 255), align="left")
        
        # ── 다음 레벨 효과 (Next)
        if lvl < data["max_lvl"]:
            next_txt = self._get_skill_effect_text(ukey, data, is_skill, lvl + 1)
            self.draw_text(f"▷ 다음 Lv.{lvl+1}: {next_txt}", (tx + 15, ty + 108), 12, (0, 255, 180), align="left")
            
            # 비용 정보
            cost_next = data["cost"] * (lvl + 1)
            currency = data.get("currency", "gold")
            cur_icon = "G" if currency == "gold" else "D"
            has_enough = (currency == "gold" and self.gold >= cost_next) or (currency == "diamond" and self.diamonds >= cost_next)
            cost_col = (255, 230, 80) if has_enough else (255, 80, 80)
            self.draw_text(f"업그레이드 비용: {cost_next}{cur_icon}", (tx + 15, ty + 132), 13, cost_col, align="left")
            
            if has_enough:
                self.draw_text(" 클릭 또는 SPACE로 구매/강화", (tx + 15, ty + 152), 12, (255, 200, 50), align="left")
            else:
                self.draw_text(f" {currency.upper()} 부족!", (tx + 15, ty + 152), 12, (255, 80, 80), align="left")
        else:
            self.draw_text(" 최대 레벨 도달! 완전 최적화됨.", (tx + 15, ty + 108), 13, (255, 220, 100), align="left")
        
        # 쿨타임 정보 (스킬인 경우)
        if is_skill:
            cd_sec = data.get("cd", 0) / 60
            self.draw_text(f"재사용 대기: {cd_sec:.0f}초", (tx + 15, ty + 175), 11, (150, 150, 180), align="left")
            max_lvl_txt = f"최대 강화: Lv.{data['max_lvl']}"
            self.draw_text(max_lvl_txt, (tx + tw - 15, ty + 175), 11, (150, 150, 180), align="right")

    def _get_skill_effect_text(self, ukey, data, is_skill, lvl):
        """주어진 레벨에서의 구체적인 스킬/업그레이드 효과 텍스트 반환"""
        if lvl == 0:
            return "미보유"
        # 영구 업그레이드 효과
        if not is_skill:
            if ukey == "shield_boost": return f"최대 쉴드 +{lvl*5}"
            elif ukey == "hp_boost":   return f"최대 HP +{lvl*10}"
            elif ukey == "speed_boost": return f"이동속도 +{lvl*3}%"
            elif ukey == "dmg_boost":   return f"공격력 +{lvl*10}%"
            elif ukey == "dash_cdr":    return f"대쉬 쿨타임 -{lvl*5}%"
            elif ukey == "xp_bonus":    return f"경험치 +{lvl*5}%"
            return data["desc"]
        # 스킬 효과
        if ukey == "nova_blast":        return f"데미지 {20+lvl*15}, 범위 {300+lvl*20}"
        elif ukey == "time_warp":       return f"지속 {2+lvl}초, 감속 {int((0.5-lvl*0.08)*100)}%"
        elif ukey == "vampirism":       return f"지속 {(600+lvl*300)//60}초, 흡혈 {int((0.3+lvl*0.1)*100)}%"
        elif ukey == "shield_overload": return f"쉴드 완충 + 공격력×1.5 ({(300+lvl*120)//60}초)"
        elif ukey == "gravity_surge":   return f"블랙홀 반경 {90+lvl*15}, 흡입 {350+lvl*40}"
        elif ukey == "stealth_cloak":   return f"은신 {(300+lvl*120)//60}초 + 속도 부스트"
        elif ukey == "shadow_extraction":return f"그림자 병사 {3+lvl//2}명 소환"
        elif ukey == "getsuga_tensho":  return f"데미지 {25+lvl*25}, 크기 {24+lvl*4}"
        elif ukey == "infinite_void":   return f"빙결 {(300+lvl*120)//60}초, 데미지 {10+lvl*10}"
        elif ukey == "titan_form":      return f"거인화 {(420+lvl*120)//60}초, 무적+짓밟기"
        elif ukey == "thunder_spear":   return f"폭발 데미지 {60+lvl*40}, 크기 {20+lvl*2}"
        elif ukey == "amaterasu":       return f"흑염 데미지 {100+lvl*150}, 범위 {150+lvl*20}"
        elif ukey == "hollow_purple":   return f"소멸빔 데미지 {300+lvl*150}, 범위 {120+lvl*15}"
        elif ukey == "gomu_gatling":    return f"5초간 난타, 데미지 {20+lvl*10}/타"
        elif ukey == "izanagi":         return f"사망 시 부활 (HP {30+lvl*20})"
        return data["desc"]

    def _draw_skill_manage_overlay(self):
        """스킬 장착 관리 오버레이 (상점에서 [I] 키로 열림)"""
        from entities import ACTIVE_SKILLS
        
        # 반투명 배경
        ov = pygame.Surface((800, 600), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 220))
        self.screen.blit(ov, (0, 0))
        
        # 타이틀
        self.draw_text("SKILL LOADOUT MANAGER", (400, 35), 32, (0, 255, 200))
        self.draw_text("장착 슬롯에 스킬을 배치하여 전투에 사용하세요", (400, 65), 14, (140, 180, 200))
        
        # ── 상단: 6개 장착 슬롯 ──
        slot_w, slot_h = 110, 80
        gap = 8
        total_w = slot_w * 6 + gap * 5
        sx_start = (800 - total_w) // 2
        sy = 90
        
        # 슬롯 바 배경
        pygame.draw.rect(self.screen, (10, 20, 35), (sx_start - 10, sy - 8, total_w + 20, slot_h + 20), border_radius=12)
        pygame.draw.rect(self.screen, (0, 180, 200), (sx_start - 10, sy - 8, total_w + 20, slot_h + 20), 2, border_radius=12)
        self.draw_text("EQUIPPED SLOTS", (400, sy - 2), 10, (0, 180, 200))
        
        mx, my = pygame.mouse.get_pos()
        
        for i in range(6):
            sx = sx_start + i * (slot_w + gap)
            slot_rect = pygame.Rect(sx, sy + 8, slot_w, slot_h - 12)
            hov = slot_rect.collidepoint(mx, my)
            
            if i < len(self.equipped_skills):
                skey = self.equipped_skills[i]
                sdata = ACTIVE_SKILLS.get(skey, {})
                lvl = self.owned_skills.get(skey, 1)
                
                bg = (30, 50, 40) if hov else (20, 35, 28)
                pygame.draw.rect(self.screen, bg, slot_rect, border_radius=8)
                pygame.draw.rect(self.screen, (0, 255, 150), slot_rect, 2, border_radius=8)
                
                # 키 번호
                self.draw_text(str(i + 1), (sx + 12, sy + 16), 12, (255, 220, 80))
                
                # 스킬 이름 (축약)
                name = sdata.get("name", skey)
                short = name[:5] if len(name) > 5 else name
                self.draw_text(short, (sx + slot_w//2, sy + 38), 14, (255, 255, 230))
                
                # 레벨
                self.draw_text(f"Lv.{lvl}", (sx + slot_w//2, sy + 56), 11, (0, 220, 150))
                
                # 클릭하면 해제
                if hov:
                    self.draw_text("클릭→해제", (sx + slot_w//2, sy + 72), 9, (255, 100, 100))
            else:
                # 빈 슬롯
                bg = (20, 25, 35) if hov else (12, 15, 22)
                pygame.draw.rect(self.screen, bg, slot_rect, border_radius=8)
                pygame.draw.rect(self.screen, (50, 60, 80), slot_rect, 1, border_radius=8)
                self.draw_text(str(i + 1), (sx + 12, sy + 16), 12, (50, 60, 75))
                self.draw_text("빈 슬롯", (sx + slot_w//2, sy + 42), 12, (50, 60, 75))
        
        # ── 하단: 보유 스킬 목록 (미장착 스킬 포함) ──
        list_y = sy + slot_h + 25
        self.draw_text("─── 보유 스킬 목록 ───", (400, list_y), 16, (200, 200, 220))
        list_y += 25
        
        owned_list = [(k, ACTIVE_SKILLS[k]) for k in self.owned_skills if k in ACTIVE_SKILLS]
        
        if not owned_list:
            self.draw_text("보유한 스킬이 없습니다. 상점에서 구매하세요!", (400, list_y + 40), 16, (120, 120, 150))
        else:
            card_w, card_h = 350, 48
            x_left, x_right = 40, 410
            row_idx = 0
            
            for idx, (skey, sdata) in enumerate(owned_list):
                col_x = x_left if idx % 2 == 0 else x_right
                row_y = list_y + (idx // 2) * (card_h + 6)
                
                if row_y > 540:
                    break  # 화면 넘침 방지
                
                is_equipped = skey in self.equipped_skills
                lvl = self.owned_skills.get(skey, 1)
                card_rect = pygame.Rect(col_x, row_y, card_w, card_h)
                hov = card_rect.collidepoint(mx, my)
                
                if is_equipped:
                    bg = (15, 40, 30) if not hov else (25, 55, 40)
                    bc = (0, 200, 120)
                    slot_idx = self.equipped_skills.index(skey) + 1
                    badge = f"[{slot_idx}]"
                    badge_col = (0, 255, 150)
                else:
                    bg = (25, 20, 35) if not hov else (40, 30, 50)
                    bc = (100, 70, 140)
                    badge = "미장착"
                    badge_col = (140, 100, 180)
                
                pygame.draw.rect(self.screen, bg, card_rect, border_radius=8)
                pygame.draw.rect(self.screen, bc, card_rect, 2 if hov else 1, border_radius=8)
                
                # 장착 상태 배지
                pygame.draw.rect(self.screen, (0,0,0), (col_x + 6, row_y + 4, 36, 14), border_radius=4)
                self.draw_text(badge, (col_x + 24, row_y + 11), 9, badge_col)
                
                # 스킬 이름 + 레벨
                self.draw_text(sdata["name"], (col_x + 50, row_y + 14), 14, (240, 240, 230), align="left")
                self.draw_text(f"Lv.{lvl}", (col_x + 50, row_y + 34), 11, bc, align="left")
                
                # 타입 표시
                stype = sdata.get("type", "active")
                type_label = "패시브" if stype == "passive" else "액티브"
                type_col = (0, 255, 150) if stype == "passive" else (255, 80, 100)
                self.draw_text(type_label, (col_x + card_w - 50, row_y + 14), 11, type_col)
                
                # 호버 안내
                if hov:
                    if is_equipped:
                        self.draw_text("클릭→해제", (col_x + card_w - 50, row_y + 34), 10, (255, 100, 100))
                    elif len(self.equipped_skills) < 6:
                        self.draw_text("클릭→장착", (col_x + card_w - 50, row_y + 34), 10, (0, 255, 120))
                    else:
                        self.draw_text("슬롯 부족", (col_x + card_w - 50, row_y + 34), 10, (255, 80, 80))
        
        # 하단 안내
        eq_n = len(self.equipped_skills)
        self.draw_text(f"장착 {eq_n}/6  |  ESC/I: 닫기  |  클릭으로 장착/해제", (400, 570), 14, (140, 160, 200))

    def _save_data(self):
        import json, os
        data = {
            "gold":     self.gold,
            "diamonds": self.diamonds,
            "crystals": self.crystals,
            "upgrades": self.upgrades,
            "owned_skills": self.owned_skills,
            "equipped_skills": self.equipped_skills,
            "last_roulette_time": self.last_roulette_time,
            "pilot_name": self.pilot_name,
            "pilot_rank": self.pilot_rank,
            "pilot_callsign": self.pilot_callsign,
            "high_score": self.high_score,
            "played_job_chapter": getattr(self, "played_job_chapter", False),
            "player_job": getattr(self.player, "job", None) if self.player else getattr(self, "saved_job", None),
            "owned_jobs": self.owned_jobs,
            "job_stats":  getattr(self.player, "job_stats", {}) if self.player else {},
        }
        try:
            with open("save_data.json", "w") as f:
                json.dump(data, f, indent=4)
        except: pass

    def _load_data(self):
        import json, os
        if os.path.exists("save_data.json"):
            try:
                with open("save_data.json", "r") as f:
                    data = json.load(f)
                    self.gold     = data.get("gold", 0)
                    self.diamonds = data.get("diamonds", 0)
                    self.crystals = data.get("crystals", 0)
                    raw_skills = data.get("owned_skills", {})
                    # 마이그레이션: 리스트 형태면 {이름: 1} 로 변환
                    if isinstance(raw_skills, list):
                        self.owned_skills = {k: 1 for k in raw_skills}
                    else:
                        self.owned_skills = raw_skills
                    
                    # ★ 장착 스킬 로드 (마이그레이션 지원)
                    raw_equipped = data.get("equipped_skills", None)
                    if raw_equipped is None:
                        # 이전 세이브: 보유 스킬 전부 장착 (최대 6개)
                        self.equipped_skills = list(self.owned_skills.keys())[:6]
                    else:
                        # 유효한 스킬만 유지
                        self.equipped_skills = [s for s in raw_equipped if s in self.owned_skills]
                    
                    self.last_roulette_time = data.get("last_roulette_time", 0)
                    self.pilot_name = data.get("pilot_name", "KIM")
                    self.pilot_rank = data.get("pilot_rank", "COMMANDER")
                    self.pilot_callsign = data.get("pilot_callsign", "RAVEN-01")
                    self.owned_jobs = data.get("owned_jobs", ["전사"])
                    saved_upg = data.get("upgrades", {})
                    for k in self.upgrades:
                        if k in saved_upg: self.upgrades[k] = saved_upg[k]
                    
                    self.high_score = data.get("high_score", 0)
                    self.played_job_chapter = data.get("played_job_chapter", False)
                    self.saved_job = data.get("player_job", None)

                    # 로드 후 플레이어에게 장착된 스킬만 부여
                    if self.player:
                        self.player.active_skills = list(self.equipped_skills)
                    # 전직 데이터 복원
                    saved_job = data.get("player_job", None)
                    if saved_job and self.player:
                        from entities import JOB_DATA
                        if saved_job in JOB_DATA:
                            self.player.apply_job(saved_job, JOB_DATA[saved_job])
                    if self.player:
                        saved_js = data.get("job_stats", {})
                        for k in self.player.job_stats:
                            if k in saved_js:
                                self.player.job_stats[k] = saved_js[k]
            except: pass

    def _draw_hud(self, progress):
        # 1. 상단 메인 HUD 프레임
        pygame.draw.rect(self.screen, (10, 15, 30), (5, 5, 790, 55), border_radius=4)
        pygame.draw.rect(self.screen, (0, 180, 255), (5, 5, 790, 55), 1, border_radius=4)
        
        # 2. XP 레벨 게이지 (프레임 상단 슬림 바)
        xp_w = int((self.player.xp / self.player.xp_to_next) * 780)
        pygame.draw.rect(self.screen, (15, 20, 35), (10, 8, 780, 5), border_radius=2)
        pygame.draw.rect(self.screen, (0, 230, 150), (10, 8, xp_w, 5), border_radius=2)
        # XP 내부 디바이더
        for i in range(1, 10):
            pygame.draw.line(self.screen, (0, 0, 0, 80), (10 + i * 78, 8), (10 + i * 78, 12))

        # 3. CORE INTEGRITY (HP) - 테크니컬 디자인
        hp_x, hp_y, hp_w, hp_h = 10, 20, 320, 22
        hp_ratio = max(0, self.player.health / self.player.max_health)
        pygame.draw.rect(self.screen, (40, 10, 20), (hp_x, hp_y, hp_w, hp_h))
        if hp_ratio > 0:
            hpc = (200, 50, 70) if hp_ratio > 0.3 else (255, 30, 30)
            if self.player.invincible > 0 and (self.player.invincible // 5) % 2 == 0: hpc = (255, 255, 255)
            if self.player.overload_timer > 0: hpc = (255, 120, 0)
            pygame.draw.rect(self.screen, hpc, (hp_x, hp_y, int(hp_w * hp_ratio), hp_h))
            # 세그먼트 눈금
            for i in range(1, 10):
                pygame.draw.line(self.screen, (0,0,0,120), (hp_x + i * (hp_w/10), hp_y), (hp_x + i * (hp_w/10), hp_y + hp_h-1))

        self.draw_text(f"선체 내구도: {int(self.player.health)} / {self.player.max_health}", (hp_x + hp_w//2, hp_y + hp_h//2), 12, (255,255,255))

        # 4. AEGIS FIELD (Shield)
        sh_x, sh_y, sh_w, sh_h = 340, 20, 220, 16
        sh_ratio = self.player.shield / self.player.max_shield if self.player.max_shield > 0 else 0
        pygame.draw.rect(self.screen, (10, 35, 60), (sh_x, sh_y, sh_w, sh_h))
        if sh_ratio > 0:
            pygame.draw.rect(self.screen, (0, 180, 255), (sh_x, sh_y, int(sh_w * sh_ratio), sh_h))
        self.draw_text(f"보호 쉴드: {int(self.player.shield)}", (sh_x + sh_w//2, sh_y + sh_h//2), 11, (100, 220, 255))

        # 5. MISSION STATS (TIME 제거됨)
        timer_x = 570
        # tl = max(0, self.current_chapter.duration - self.game_time//60)
        # t_str = f"{tl//60:02d}:{tl%60:02d}"
        # self.draw_text(t_str, (timer_x + 40, 31), 24, (255, 255, 100))
        self.draw_text(f"G: {self.gold:,}  D: {self.diamonds:,}", (timer_x + 140, 20), 16, (255, 230, 80))
        self.draw_text(f"점수: {self.player.score:,}", (timer_x + 140, 38), 13, (220, 220, 220))
        
        # 6. SKILL SLOT BAR (왼쪽 사이드 수직 슬롯 - 전투 UI 개선)
        from entities import ACTIVE_SKILLS
        slot_w, slot_h = 60, 56
        gap = 8
        total_h = slot_h * 6 + gap * 5
        bar_x = 12
        bar_y = 70  # HUD 바로 아래 왼쪽 사이드바
        
        mx, my = self.mouse_pos
        hovered_skill = None

        # 슬롯 바 배경 (글래스모피즘 효과)
        try:
            bar_bg = pygame.Surface((slot_w + 16, total_h + 16), pygame.SRCALPHA)
            bar_bg.fill((10, 15, 30, 180))
            self.screen.blit(bar_bg, (bar_x - 8, bar_y - 8))
        except: pass
        pygame.draw.rect(self.screen, (0, 180, 255, 100), (bar_x - 8, bar_y - 8, slot_w + 16, total_h + 16), 1, border_radius=10)

        skills = self.player.active_skills if self.player else []
        for i in range(6):
            sx = bar_x
            sy = bar_y + i * (slot_h + gap)
            slot_rect = pygame.Rect(sx, sy, slot_w, slot_h)
            is_hov = slot_rect.collidepoint(mx, my)

            if i < len(skills):
                skey = skills[i]
                sdata = ACTIVE_SKILLS.get(skey, {})
                cd = self.player.skill_cooldowns.get(skey, 0)
                max_cd = sdata.get("cd", 1)
                
                if is_hov:
                    hovered_skill = (skey, sdata, cd)

                # 슬롯 배경 (쿨타임 기반 색상 변화)
                bg_col = (45, 20, 15) if cd > 0 else (20, 35, 65)
                if is_hov: bg_col = tuple(min(255, c + 40) for c in bg_col)
                pygame.draw.rect(self.screen, bg_col, slot_rect, border_radius=8)

                # 쿨타임 오버레이 (아래에서 위로 차오름)
                if cd > 0:
                    cd_ratio = cd / max_cd
                    fill_h = int(slot_h * cd_ratio)
                    pygame.draw.rect(self.screen, (100, 30, 20, 160), (sx, sy + slot_h - fill_h, slot_w, fill_h), border_radius=8)

                # 테두리 (활성화 상태 강조)
                border_col = (255, 215, 0) if cd == 0 else (120, 60, 40)
                if is_hov: border_col = (255, 255, 255)
                pygame.draw.rect(self.screen, border_col, slot_rect, 2 if is_hov else 1, border_radius=8)

                # 단축키 번호 (좌상단)
                self.draw_text(str(i + 1), (sx + 8, sy + 8), 11, (255, 255, 120))

                # 스킬 아이콘 (중앙 정렬)
                icon_col = sdata.get("color", (0, 200, 255))
                pygame.draw.circle(self.screen, icon_col, (sx + slot_w//2, sy + 22), 8)
                pygame.draw.circle(self.screen, (255, 255, 255), (sx + slot_w//2, sy + 22), 8, 1)

                # 스킬 이름 (하단 작게)
                name = sdata.get("name", skey)
                short = name[:4] if len(name) > 4 else name
                self.draw_text(short, (sx + slot_w // 2, sy + 44), 10, (230, 230, 230))

                # 쿨타임 수치 표시
                if cd > 0:
                    cd_sec = f"{cd / 60:.1f}s"
                    self.draw_text(cd_sec, (sx + slot_w // 2, sy + 24), 13, (255, 255, 255))
                elif is_hov:
                    self.draw_text("READY", (sx + slot_w // 2, sy + 24), 11, (0, 255, 150))
            else:
                # 미장착 빈 슬롯
                pygame.draw.rect(self.screen, (15, 15, 25), slot_rect, border_radius=8)
                pygame.draw.rect(self.screen, (50, 50, 70), slot_rect, 1, border_radius=8)
                self.draw_text(str(i + 1), (sx + 8, sy + 8), 11, (60, 60, 80))

        # ★ 상단 스킬 능력치 정보창 (유저 요청: 위쪽에 보이게)
        if hovered_skill:
            skey, sdata, cd = hovered_skill
            lvl = self.owned_skills.get(skey, 1)
            eff_text = self._get_skill_effect_text(skey, sdata, True, lvl)
            
            # 상단 중앙 메인 HUD 아래에 부유하는 카드 형태
            tw, th = 420, 50
            tx, ty = 400 - tw//2, 70
            try:
                tip_bg = pygame.Surface((tw, th), pygame.SRCALPHA)
                tip_bg.fill((10, 10, 25, 220))
                self.screen.blit(tip_bg, (tx, ty))
            except: pass
            pygame.draw.rect(self.screen, (0, 230, 255), (tx, ty, tw, th), 1, border_radius=10)
            
            # 스킬 이름 및 레벨
            self.draw_text(f"「{sdata['name']}」 Lv.{lvl}", (400, ty + 15), 15, (255, 215, 50))
            # 스킬 구체적 효과
            self.draw_text(eff_text, (400, ty + 35), 12, (180, 240, 255))

        #  HUD 연결 테크니컬 라인 (Integrated Frame)
        pygame.draw.line(self.screen, (150, 80, 0), (335, 20), (335, 45), 1) # HP - Shield 구분
        pygame.draw.line(self.screen, (150, 80, 0), (565, 20), (565, 45), 1) # Shield - Stats 구분

        form = SHIP_FORMS.get(self.player.ship_form, SHIP_FORMS["fighter"])
        dash_ready = "●" if self.player.dash_cd==0 else f"○{self.player.dash_cd//10}"
        dim_txt  = "심해" if self.abyss_active else ("공허" if self.dimension=="VOID" else "물질")
        dive_txt = f"  ↓{int(self.player.dive_depth)}%" if self.player.dive_active else ""
        self.draw_text(
            f"LV:{self.player.level}  [{dim_txt}]  {self.player.weapon['name']}  {dash_ready}{dive_txt}",
            (210,52),16,(255,230,80))
        self.draw_text(f"[{form['name']}]",(620,52),14,(180,220,255))
        cfg_col = (0, 220, 255) if self.settings_open else (70, 90, 110)
        self.draw_text(" ESC/TAB", (760, 52), 12, cfg_col)

        # 현재 직업 + 등급 표시 (전직 후에만)
        if self.player.job:
            from entities import JOB_DATA
            jd = JOB_DATA.get(self.player.job, {})
            jcol = jd.get("color", (255, 220, 80))
            tier_idx  = getattr(self.player, "job_tier", 0)
            tier_name = JOB_TIER_DATA["names"][tier_idx]
            tier_col  = JOB_TIER_DATA["colors"][tier_idx]
            self.draw_text(f"[{self.player.job}]", (72, 122), 13, jcol, align="left")
            self.draw_text(tier_name, (72, 136), 11, tier_col, align="left")
            # 다음 등급까지 처치 수 표시
            kills_req = JOB_TIER_DATA["kills"]
            max_tier  = len(kills_req) - 1
            if tier_idx < max_tier:
                needed = kills_req[tier_idx + 1]
                cur_k  = getattr(self.player, "job_kills", 0)
                self.draw_text(f"{cur_k}/{needed}", (72, 148), 10, (140, 140, 160), align="left")

        # ── 위협 수준 & 서지 경고 (우하단) ──────────────────────────
        enemy_count = len(self.enemies)
        if enemy_count >= 15:
            threat = min(5, enemy_count // 6)
            t_colors = [(255,220,0),(255,180,0),(255,120,0),(255,60,0),(255,20,20)]
            t_col = t_colors[threat - 1]
            t_label = ["LOW","MED","HIGH","CRIT","MAX"][threat - 1]
            threat_x = 570
            self.draw_text(f"THREAT [{t_label}] ×{enemy_count}", (threat_x + 140, 52), 12, t_col)

        if self.surge_warning > 0:
            alpha = min(255, self.surge_warning * 3)
            pulse = abs(math.sin(self.game_time * 0.15))
            surge_col = (int(255 * pulse), int(80 * pulse), int(80 * pulse))
            self.draw_text("⚠  ELITE SURGE  ⚠", (400, 575), 18, surge_col)

        self._draw_weapon_inventory()

    def _draw_weapon_inventory(self):
        """해금된 무기를 하단 중앙에 클릭 가능한 슬롯으로 표시."""
        unlocked = self.player.unlocked_weapons
        if not unlocked:
            return

        slot_w, slot_h = 54, 44
        gap = 6
        total_w = len(unlocked) * (slot_w + gap) - gap
        start_x = 400 - total_w // 2
        bar_y = 532

        # 배경 패널
        pad = 8
        panel_rect = pygame.Rect(start_x - pad, bar_y - pad, total_w + pad * 2, slot_h + pad * 2)
        pygame.draw.rect(self.screen, (8, 12, 28), panel_rect, border_radius=6)
        pygame.draw.rect(self.screen, (0, 140, 220), panel_rect, 1, border_radius=6)

        mx, my = self.mouse_pos
        self._weapon_inv_slots.clear()

        for i, wkey in enumerate(unlocked):
            wdata = WEAPONS.get(wkey, {})
            sx = start_x + i * (slot_w + gap)
            slot_rect = pygame.Rect(sx, bar_y, slot_w, slot_h)
            self._weapon_inv_slots.append((slot_rect, wkey))

            is_sel = (wkey == self.player.weapon_key)
            is_hov = slot_rect.collidepoint(mx, my)

            # 슬롯 배경
            if is_sel:
                bg = (30, 60, 110)
            elif is_hov:
                bg = (20, 40, 70)
            else:
                bg = (12, 18, 36)
            pygame.draw.rect(self.screen, bg, slot_rect, border_radius=5)

            # 테두리
            border = (0, 255, 180) if is_sel else ((180, 220, 255) if is_hov else (40, 60, 90))
            pygame.draw.rect(self.screen, border, slot_rect, 2 if is_sel else 1, border_radius=5)

            # 무기 색 아이콘 (원)
            icon_col = wdata.get("color_p", (120, 120, 255))
            cx_icon = sx + slot_w // 2
            cy_icon = bar_y + 16
            pygame.draw.circle(self.screen, icon_col, (cx_icon, cy_icon), 7)
            if is_sel:
                pygame.draw.circle(self.screen, (255, 255, 255), (cx_icon, cy_icon), 7, 1)

            # 무기 이름 (짧게)
            name = wdata.get("name", wkey)
            short = name[:5] if len(name) > 5 else name
            name_col = (255, 255, 100) if is_sel else (200, 200, 200)
            self.draw_text(short, (cx_icon, bar_y + 34), 10, name_col)

            # 호버 툴팁: 무기 전체 이름 + 데미지/쿨타임
            if is_hov and not is_sel:
                dmg = wdata.get("dmg", "?")
                cd = wdata.get("cooldown", "?")
                tip = f"{wdata.get('name', wkey)}  dmg:{dmg} cd:{cd}"
                tip_x = min(max(cx_icon, 80), 720)
                self.draw_text(tip, (tip_x, bar_y - 14), 11, (255, 230, 100))

        # 라벨
        self.draw_text("무기 인벤토리", (400, bar_y + slot_h + 10), 10, (80, 120, 160))

    def _draw_minimap(self):
        mmx,mmy = 668,488; mmw,mmh = 124,94; scale=0.038
        try:
            surf = pygame.Surface((mmw,mmh), pygame.SRCALPHA)
            surf.fill((0,0,0,140))
            self.screen.blit(surf,(mmx,mmy))
        except Exception:
            pass
        pygame.draw.rect(self.screen,(55,55,75),(mmx,mmy,mmw,mmh),1)
        cx=mmx+mmw//2; cy=mmy+mmh//2; pw=self.player.world_pos
        for bh in self.blackholes:
            dx=int((bh.world_pos.x-pw.x)*scale); dy=int((bh.world_pos.y-pw.y)*scale)
            sx=cx+dx; sy=cy+dy
            if mmx<=sx<=mmx+mmw and mmy<=sy<=mmy+mmh:
                pygame.draw.circle(self.screen,(180,0,255),(sx,sy),4)
        for enemy in self.enemies:
            if enemy.dimension_type==self.dimension or self.abyss_active:
                dx=int((enemy.world_pos.x-pw.x)*scale); dy=int((enemy.world_pos.y-pw.y)*scale)
                sx=cx+dx; sy=cy+dy
                if mmx<=sx<=mmx+mmw and mmy<=sy<=mmy+mmh:
                    col=(255,80,80) if enemy.max_hp>=20 else (255,150,50)
                    pygame.draw.circle(self.screen,col,(sx,sy),2)
        for item in self.items:
            dx=int((item.world_pos.x-pw.x)*scale); dy=int((item.world_pos.y-pw.y)*scale)
            sx=cx+dx; sy=cy+dy
            if mmx<=sx<=mmx+mmw and mmy<=sy<=mmy+mmh:
                pygame.draw.circle(self.screen,(0,255,100),(sx,sy),2)
        pygame.draw.circle(self.screen,(0,255,255),(cx,cy),3)
        pygame.draw.rect(self.screen,(60,60,80),(mmx,mmy,mmw,mmh),1)

    def _draw_form_select(self):
        ov = pygame.Surface((800,600),pygame.SRCALPHA)
        ov.fill((0,0,0,190))
        self.screen.blit(ov,(0,0))
        self.draw_text("── 우주선 변형 선택 ──",(400,150),38,(0,220,255))
        self.draw_text("← → 이동  ENTER/F 확정  ESC 취소",(400,190),18,(150,150,200))
        forms = self.player.unlocked_forms
        n = len(forms)
        for i,fk in enumerate(forms):
            fd   = SHIP_FORMS[fk]
            sel  = (i == self.form_select_idx)
            cx   = 400 + (i - n//2) * 160 + (80 if n%2==0 else 0)
            cy   = 350
            card = pygame.Rect(cx-68, cy-80, 136, 160)
            bg   = (40,40,70) if sel else (20,20,40)
            bc   = (255,220,50) if sel else (80,80,120)
            pygame.draw.rect(self.screen, bg, card, border_radius=10)
            pygame.draw.rect(self.screen, bc, card, 2 if sel else 1, border_radius=10)
            poly = fd["poly"]
            offset_x = cx-18; offset_y = cy-55
            shifted = [(p[0]+offset_x, p[1]+offset_y) for p in poly]
            if len(shifted)>=3:
                col = fd["color_p"] if self.dimension=="PHYSICAL" else fd["color_v"]
                pygame.draw.polygon(self.screen, col, shifted)
                pygame.draw.polygon(self.screen, (255,255,255), shifted, 1)
            self.draw_text(fd["name"].split("(")[0].strip(),(cx,cy+18),16,
                           (255,230,50) if sel else (180,180,220))
            self.draw_text(fd["desc"][:20],(cx,cy+40),12,(150,180,200))
            spd = fd["speed_mult"]; dmg = fd["dmg_mult"]
            self.draw_text(f"SPD×{spd:.1f}  DMG×{dmg:.1f}",(cx,cy+60),12,(200,200,150))
            if fk == self.player.ship_form:
                self.draw_text("현재",(cx,cy+80),13,(100,255,100))

    def _draw_job_select_overlay(self):
        """전직 선택 오버레이 — 2단계 귀여운 애니메이션 UI"""
        from entities import JOB_DATA

        t = self.job_select_timer
        self.job_select_timer += 1
        PHASE_REVEAL = 90   # Phase 1 지속 프레임

        # ── 배경 ──────────────────────────────────────────
        ov = pygame.Surface((800, 600), pygame.SRCALPHA)
        bg_alpha = min(220, int(t * 4))
        ov.fill((5, 8, 20, bg_alpha))
        self.screen.blit(ov, (0, 0))

        # 배경 별빛 파티클 (귀여운 느낌)
        rng = random.Random(42)
        for _ in range(30):
            sx = rng.randint(0, 800)
            sy = rng.randint(0, 600)
            twinkle = abs(math.sin((t * 0.05) + rng.random() * 6.28))
            star_a = int(twinkle * 150 + 30)
            ss = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(ss, (200, 200, 255, star_a), (2, 2), 2)
            self.screen.blit(ss, (sx, sy))

        # ═══════════════════════════════════════════════
        #  PHASE 1 — 데이터 분석 스캔 (0~89프레임)
        # ═══════════════════════════════════════════════
        if t < PHASE_REVEAL:
            progress = t / PHASE_REVEAL  # 0.0 ~ 1.0

            # 타이틀 페이드인
            title_a = min(255, int(t * 6))
            title_surf = pygame.Surface((500, 50), pygame.SRCALPHA)
            # 타이틀 텍스트를 surface에 그린 후 alpha 적용
            self.draw_text("★ 플레이어 데이터 분석 중 ★", (400, 50), 30,
                           (255, 220, 80, title_a) if title_a < 255 else (255, 220, 80))

            # 스캔 바 애니메이션
            bar_x, bar_y, bar_w, bar_h = 150, 90, 500, 12
            pygame.draw.rect(self.screen, (30, 40, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            filled = int(bar_w * progress)
            if filled > 0:
                scan_col = (
                    int(80 + 175 * progress),
                    int(200 - 100 * progress),
                    int(255 - 100 * progress)
                )
                pygame.draw.rect(self.screen, scan_col, (bar_x, bar_y, filled, bar_h), border_radius=6)
            # 스캔 광 이펙트
            if filled > 4:
                glow = pygame.Surface((8, bar_h + 8), pygame.SRCALPHA)
                glow.fill((255, 255, 255, 120))
                self.screen.blit(glow, (bar_x + filled - 4, bar_y - 4))
            self.draw_text(f"분석중... {int(progress * 100)}%", (400, 115), 13, (160, 200, 255))

            # 플레이 스탯 순차 공개 (프레임에 따라 하나씩 등장)
            js = self.player.job_stats
            stats_list = [
                ("⚔  근접 처치", js["melee_kills"],   (255, 140, 100)),
                ("🎯  원거리 처치", js["range_kills"], (100, 200, 255)),
                ("💨  대시 횟수",  js["dash_count"],   (150, 255, 180)),
                ("✨  스킬 사용",  js["skill_uses"],   (220, 150, 255)),
                ("🌀  차원 이동",  js["dim_switches"], (100, 220, 255)),
                ("🔥  최대 콤보",  js["max_combo"],    (255, 220, 60)),
            ]
            reveal_interval = PHASE_REVEAL / (len(stats_list) + 2)
            for si, (label, val, col) in enumerate(stats_list):
                reveal_at = reveal_interval * (si + 1)
                if t >= reveal_at:
                    row_alpha = min(255, int((t - reveal_at) * 15))
                    sy_pos = 148 + si * 28
                    # 배경 바
                    bar_bg = pygame.Surface((480, 22), pygame.SRCALPHA)
                    bar_bg.fill((20, 30, 50, row_alpha // 2))
                    self.screen.blit(bar_bg, (160, sy_pos - 2))
                    # 값 바 (길이는 값에 비례, 최대 200px)
                    val_w = min(200, val * 4 + 20)
                    val_bar = pygame.Surface((val_w, 4), pygame.SRCALPHA)
                    val_bar.fill((*col, row_alpha))
                    self.screen.blit(val_bar, (360, sy_pos + 10))
                    # 텍스트
                    r, g, b = col
                    self.draw_text(f"{label}  :  {val}", (310, sy_pos + 6), 13,
                                   (min(255,r), min(255,g), min(255,b)))

            return  # Phase 1 끝

        # ═══════════════════════════════════════════════
        #  PHASE 2 — 직업 카드 슬라이드 인 & 선택
        # ═══════════════════════════════════════════════
        t2 = t - PHASE_REVEAL  # Phase2 경과 프레임

        # 타이틀
        pulse = 0.5 + 0.5 * math.sin(t * 0.08)
        title_r = int(240 + 15 * pulse)
        title_g = int(200 + 20 * pulse)
        self.draw_text("✦  전직 의식  ✦", (400, 36), 34, (title_r, title_g, 60))
        self.draw_text("당신의 플레이 스타일이 직업을 결정했습니다!", (400, 76), 15, (180, 190, 230))

        # 마우스 위치 (호버 감지)
        mx, my = pygame.mouse.get_pos()

        card_w, card_h = 220, 248
        total_w = card_w * 3 + 24
        start_x = (800 - total_w) // 2

        # 직업 아이콘 문자 맵
        job_icons = {
            "전사": "⚔", "저격수": "🎯", "파일럿": "🚀", "마법사": "✨",
            "흡혈귀": "🧛", "기계공": "🔧", "탱커": "🛡", "광속": "⚡",
            "차원술사": "🌀", "학살자": "💀",
        }

        for i, jkey in enumerate(self.job_select_choices):
            if jkey not in JOB_DATA:
                continue
            jd = JOB_DATA[jkey]

            # 슬라이드 인 이징 (ease-out cubic)
            slide_delay = i * 12  # 카드마다 엇갈리게
            card_t = max(0, t2 - slide_delay)
            raw = min(1.0, card_t / 35.0)
            ease = 1 - (1 - raw) ** 3  # ease-out cubic
            slide_y = int((1 - ease) * 300)  # 300px 아래서 올라옴

            cx = start_x + i * (card_w + 12)
            base_cy = 98 + slide_y

            # 호버 감지 → 카드 살짝 위로
            hovered = (cx <= mx <= cx + card_w and base_cy <= my <= base_cy + card_h)
            cy = base_cy - (10 if hovered else 0)

            # ── 카드 그림자 (호버시 더 진하게) ──
            shadow = pygame.Surface((card_w + 8, card_h + 8), pygame.SRCALPHA)
            shadow_a = 120 if hovered else 60
            pygame.draw.rect(shadow, (0, 0, 0, shadow_a), (4, 4, card_w, card_h), border_radius=16)
            self.screen.blit(shadow, (cx - 4, cy))

            # ── 카드 배경 ──
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (18, 24, 42, 240), (0, 0, card_w, card_h), border_radius=14)
            self.screen.blit(card_surf, (cx, cy))

            # ── 헤더 색상 띠 ──
            r, g, b = jd["color"]
            header_surf = pygame.Surface((card_w, 52), pygame.SRCALPHA)
            pygame.draw.rect(header_surf, (*jd["color"], 80), (0, 0, card_w, 52), border_radius=14)
            # 하단 그라데이션 느낌 (밑 테두리 없애기)
            pygame.draw.rect(header_surf, (*jd["color"], 40), (0, 30, card_w, 22))
            self.screen.blit(header_surf, (cx, cy))

            # ── 테두리 (호버/펄스) ──
            if hovered:
                border_pulse = 0.7 + 0.3 * math.sin(t * 0.2)
                bw = int(3 + border_pulse * 2)
                border_col = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
            else:
                border_pulse = 0.5 + 0.5 * math.sin(t * 0.07 + i * 1.2)
                bw = 2
                border_col = (int(r * 0.7 + r * 0.3 * border_pulse),
                               int(g * 0.7 + g * 0.3 * border_pulse),
                               int(b * 0.7 + b * 0.3 * border_pulse))
            pygame.draw.rect(self.screen, border_col, (cx, cy, card_w, card_h), bw, border_radius=14)

            # ── 아이콘 원 ──
            icon_x = cx + card_w // 2
            icon_y = cy + 28
            icon_r = 22 if hovered else 20
            pygame.draw.circle(self.screen, jd["color"], (icon_x, icon_y), icon_r)
            pygame.draw.circle(self.screen, (255, 255, 255), (icon_x, icon_y), icon_r, 2)
            icon_char = job_icons.get(jkey, "★")
            self.draw_text(icon_char, (icon_x, icon_y), 18, (255, 255, 255))

            # ── 번호 배지 (좌상단) ──
            badge_col = jd["color"]
            pygame.draw.circle(self.screen, badge_col, (cx + 18, cy + 18), 13)
            pygame.draw.circle(self.screen, (255, 255, 255), (cx + 18, cy + 18), 13, 1)
            self.draw_text(str(i + 1), (cx + 18, cy + 18), 15, (0, 0, 0))

            # ── 직업 이름 ──
            name_y = cy + 68  # 아이콘 원 하단(cy+48)과의 간격 확보
            self.draw_text(jd["name"], (cx + card_w // 2, name_y), 22, jd["color"])

            # ── 설명 (카드 폭 초과 방지: ". " 기준 2줄 분리) ──
            desc_raw = jd["desc"]
            desc_parts = desc_raw.split(". ", 1)
            if len(desc_parts) == 2:
                self.draw_text(desc_parts[0] + ".", (cx + card_w // 2, name_y + 20), 10, (190, 195, 220))
                self.draw_text(desc_parts[1],       (cx + card_w // 2, name_y + 34), 10, (190, 195, 220))
                line_y = cy + 122
            else:
                self.draw_text(desc_raw, (cx + card_w // 2, name_y + 22), 10, (190, 195, 220))
                line_y = cy + 110

            # ── 구분선 ──
            pygame.draw.line(self.screen, (*jd["color"], 120),
                             (cx + 14, line_y), (cx + card_w - 14, line_y), 1)

            # ── 버프 섹션 ──
            self.draw_text("▲ BUFF", (cx + card_w // 2, line_y + 13), 11, (80, 230, 120))
            buff_lines = jd["buff"].split(" · ")
            for li, line in enumerate(buff_lines[:2]):
                self.draw_text(line, (cx + card_w // 2, line_y + 27 + li * 14), 10, (150, 235, 175))

            # ── 너프 섹션 ──
            nerf_y = line_y + 62
            self.draw_text("▼ NERF", (cx + card_w // 2, nerf_y), 11, (230, 80, 80))
            nerf_raw = jd["nerf"]
            nerf_parts = nerf_raw.split(" · ", 1)
            if len(nerf_parts) == 2:
                self.draw_text(nerf_parts[0], (cx + card_w // 2, nerf_y + 13), 10, (240, 160, 160))
                self.draw_text(nerf_parts[1], (cx + card_w // 2, nerf_y + 25), 10, (240, 160, 160))
            else:
                self.draw_text(nerf_raw, (cx + card_w // 2, nerf_y + 14), 10, (240, 160, 160))

            # ── 키 배지 (하단) ──
            key_y = cy + card_h - 22
            key_col = (255, 230, 60) if hovered else (200, 180, 40)
            key_bg = pygame.Surface((80, 22), pygame.SRCALPHA)
            pygame.draw.rect(key_bg, (*key_col, 50 if not hovered else 90), (0, 0, 80, 22), border_radius=8)
            self.screen.blit(key_bg, (cx + card_w // 2 - 40, key_y - 3))
            self.draw_text(f"[{i+1}] 또는 클릭", (cx + card_w // 2, key_y + 8), 11, key_col)

        # ── 하단 안내 ──
        bottom_y = 360 + (8 if len(self.job_select_choices) > 0 else 0)
        blink = int(abs(math.sin(t * 0.07)) * 80 + 175)
        self.draw_text("직업은 영구 적용됩니다  ·  신중하게 선택하세요!",
                       (400, bottom_y + 10), 13, (255, 180, 60))
        self.draw_text("[ 1 / 2 / 3 ] 키 또는 카드 클릭으로 선택",
                       (400, bottom_y + 32), 13, (blink, blink, 100))

        # ── 현재 스탯 미리보기 박스 ──
        pv_y = bottom_y + 56
        pv_surf = pygame.Surface((480, 88), pygame.SRCALPHA)
        pygame.draw.rect(pv_surf, (12, 18, 35, 200), (0, 0, 480, 88), border_radius=10)
        pygame.draw.rect(pv_surf, (60, 80, 130, 160), (0, 0, 480, 88), 1, border_radius=10)
        self.screen.blit(pv_surf, (160, pv_y))
        self.draw_text("현재 스탯 미리보기", (400, pv_y + 12), 12, (140, 180, 255))
        self.draw_text(
            f"HP {self.player.health}/{self.player.max_health}  "
            f"쉴드 {int(self.player.shield)}/{self.player.max_shield}  "
            f"LV {self.player.level}  킬 {self.player.kill_count}",
            (400, pv_y + 34), 12, (190, 215, 255))
        self.draw_text(
            f"점수 {self.player.score:,}  콤보 최고 {self.player.max_combo}",
            (400, pv_y + 54), 12, (190, 215, 255))
        self.draw_text(
            f"현재 직업: {'없음' if not self.player.job else self.player.job}",
            (400, pv_y + 72), 12, (255, 215, 90))

    def _draw_levelup_overlay(self):
        ov = pygame.Surface((800,600),pygame.SRCALPHA)
        ov.fill((0,0,0,175))
        self.screen.blit(ov,(0,0))
        self.draw_text(f"LEVEL UP!  LV {self.player.level}",(400,170),52,(255,230,50))
        self.draw_text("보너스 선택",(400,230),26,(200,200,200))
        labels = {
            "weapon": lambda v: f"무기 해금: {WEAPONS[v]['name']}",
            "form":   lambda v: f"변형 해금: {SHIP_FORMS[v]['name'].split('(')[0]}",
            "stat":   lambda v: {"cooldown":"사격 속도 +1","maxhp":"최대 HP +25  쉴드 +10","robot":"로봇 동반자 소환"}.get(v,v),
        }
        for i,(ctype,cval) in enumerate(self.levelup_choices):
            y=300+i*78; text=labels[ctype](cval)
            pygame.draw.rect(self.screen,(26,26,46),(170,y-22,460,58),border_radius=10)
            pygame.draw.rect(self.screen,(80,80,130),(170,y-22,460,58),1,border_radius=10)
            self.draw_text(f"[{i+1}]  {text}",(400,y+8),26,(255,220,60))

    def _draw_death(self):
        self.screen.fill((18, 4, 8))
        rng = random.Random(self.game_time)
        for _ in range(60):
            x=rng.randint(0,800); y=rng.randint(0,600)
            pygame.draw.circle(self.screen, (rng.randint(60, 140), 10, 10), (x,y), 1)
        
        # 상단 헤더
        pygame.draw.line(self.screen, (255, 50, 50), (100, 180), (700, 180), 2)
        self.draw_text("MISSION STATUS: FAILURE", (400, 155), 24, (255, 80, 80))
        self.draw_text("미션 종료", (400, 230), 62, (255, 40, 40))
        
        if self.player:
            # 통계 박스
            pygame.draw.rect(self.screen, (30, 10, 10), (200, 300, 400, 120), border_radius=10)
            pygame.draw.rect(self.screen, (150, 40, 40), (200, 300, 400, 120), 1, border_radius=10)
            
            self.draw_text(f"최종 점수: {self.player.score:,}", (400, 325), 28, (255, 220, 80))
            self.draw_text(f"KILLS: {self.player.kill_count}  |  MAX COMBO: {self.player.max_combo}", (400, 365), 16, (200, 180, 180))
            self.draw_text(f"REACHED LEVEL: {self.player.level}", (400, 390), 16, (180, 220, 255))
            
            # 획득 보상 표시
            if hasattr(self, "last_death_rewards"):
                rw = self.last_death_rewards
                reward_txt = f" 보상 획득:  +{rw['gold']:,} GOLD   +{rw['dia']:,} DIAMOND"
                self.draw_text(reward_txt, (400, 420), 18, (0, 255, 150))
            
        self.draw_text(f"HIGH SCORE: {self.high_score:,}", (400, 445), 20, (140, 160, 200))
        
        # 하단 푸터
        pygame.draw.line(self.screen, (255, 50, 50), (100, 500), (700, 500), 2)
        pulse = int(140 + 60 * math.sin(self.game_time * 0.1))
        self.draw_text("[R] 키를 눌러 베이스로 복귀", (400, 530), 22, (pulse, pulse, pulse))

    def _draw_win(self):
        self.screen.fill((4, 18, 12))
        rng = random.Random(self.game_time)
        for _ in range(80):
            x=rng.randint(0,800); y=rng.randint(0,600)
            pygame.draw.circle(self.screen, (0, rng.randint(80, 160), 100), (x,y), 1)
            
        # 상단 헤더
        pygame.draw.line(self.screen, (0, 255, 150), (100, 160), (700, 160), 2)
        self.draw_text("MISSION STATUS: COMPLETE", (400, 135), 24, (0, 255, 180))
        self.draw_text("챕터 클리어!", (400, 215), 58, (255, 255, 255))
        
        if self.player:
            # 보상 박스
            pygame.draw.rect(self.screen, (10, 40, 30), (180, 280, 440, 130), border_radius=12)
            pygame.draw.rect(self.screen, (0, 255, 120), (180, 280, 440, 130), 1, border_radius=12)
            
            self.draw_text(f"획득 점수: {self.player.score:,}", (400, 310), 30, (255, 220, 80))
            self.draw_text(f"ELIMINATED: {self.player.kill_count}  |  MAX COMBO: {self.player.max_combo}", (400, 355), 16, (180, 220, 180))
            if self.rift_boss_kill_count > 0:
                self.draw_text(f" RIFT BOSS ELIMINATED: {self.rift_boss_kill_count} UNITS", (400, 385), 14, (200, 120, 255))
            
        self.draw_text(f"PERSONAL BEST: {self.high_score:,}", (400, 435), 20, (140, 180, 160))
        
        # 하단 푸터
        pygame.draw.line(self.screen, (0, 255, 150), (100, 490), (700, 490), 2)
        pulse = int(180 + 75 * math.sin(self.game_time * 0.1))
        self.draw_text("[M] 키를 눌러 베이스로 복귀", (400, 525), 22, (pulse, pulse, pulse))

    # ─────────────────────────────────────
    def _get_font(self, size):
        if not hasattr(self,"_font_cache"): self._font_cache={}
        if size not in self._font_cache:
            import os
            # 인간스러운 느낌의 폰트 (궁서, 바탕, 나눔펜 등) 위주로 후보 구성
            candidates=["C:/Windows/Fonts/gungsuh.ttc", "C:/Windows/Fonts/batang.ttc",
                        "C:/Windows/Fonts/H2PORM.TTF",  # 휴먼옛체/휴먼편지체 등
                        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]
            font=None
            for path in candidates:
                if os.path.exists(path):
                    try: font=pygame.font.Font(path,size); break
                    except Exception: continue
            if font is None:
                for name in ["궁서", "gungsuh", "batang", "바탕", "malgun gothic"]:
                    try:
                        f=pygame.font.SysFont(name,size)
                        if f: font=f; break
                    except Exception: continue
            if font is None: font=pygame.font.SysFont(None,size)
            self._font_cache[size]=font
        return self._font_cache[size]

    def draw_text(self, text, pos, size, color=(255,255,255), align="center", bg=None):
        font=self._get_font(size)
        img =font.render(text,True,color)
        if align == "left":
            rect=img.get_rect(midleft=pos)
        elif align == "right":
            rect=img.get_rect(midright=pos)
        else:
            rect=img.get_rect(center=pos)
        if bg:
            pad = 4
            bg_rect = rect.inflate(pad*2, pad*2)
            pygame.draw.rect(self.screen, bg, bg_rect)
        self.screen.blit(img,rect)

if __name__ == "__main__":
    from main import main
    main()