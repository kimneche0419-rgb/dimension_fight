import pygame
import random
import math
from entities import (Player, Enemy, Projectile, EnemyProjectile, Gem,
                      Structure, Fluid, RobotCompanion, PickupItem,
                      Particle, Blackhole, WEAPONS, WEAPON_ORDER,
                      WEAPON_UNLOCK_LEVEL, ENEMY_DATA, ITEM_DATA, SHIP_FORMS,
                      SHIP_COLORS, SETTINGS)
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

    def draw(self, surface, camera_offset, dimension, abyss=False):
        W, H = 800, 600
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
        self.special   = special or []   # 특수 규칙 리스트

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

        # ── 차원 시스템 ──────────────────────────────
        self.abyss_active   = False   # 블랙홀 소멸 후 심해 차원 활성
        self.abyss_timer    = 0       # 남은 프레임 (3600=60초)
        self.ABYSS_DURATION = 3600

        # ── 블랙홀 ───────────────────────────────────
        self.blackholes    = []
        self.bh_spawn_cd   = 0        # 블랙홀 쿨타임

        # ── 색상 선택 UI ──────────────────────────────
        self.color_select_active  = False
        self.color_select_idx     = 0
        self.pending_chapter_id   = None   # 색상 선택 후 시작할 챕터

        # ── 제3차원 (균열 차원) ────────────────────────
        self.rift_active      = False   # 블랙홀 흡입 후 제3차원 전투
        self.rift_boss        = None    # 균열 수호자 Enemy 인스턴스
        self.rift_enemies     = pygame.sprite.Group()
        self.rift_projectiles = pygame.sprite.Group()
        self.rift_ep          = pygame.sprite.Group()
        self.rift_particles   = []
        self.rift_player_hp_save  = 100
        self.rift_player_pos_save = Vector2(0,0)
        self.rift_timer       = 0

        # ── 블랙홀 흡입 트랜지션 ──────────────────────
        self.bh_suck_timer   = 0        # >0 이면 흡입 연출 중
        self.bh_suck_target  = None     # 흡입하는 블랙홀
        self.bh_flash_timer  = 0        # 화이트 플래시

        # ── 블랙홀 보스 처치 누적 (능력치 상향용) ────
        self.rift_boss_kill_count = 0   # 처치한 균열 보스 수

        # 우주선 변형 선택 UI
        self.form_select_active = False
        self.form_select_idx    = 0

        # ── 메인 메뉴 룰렛 ─────────────────────────────
        self.roulette_active   = False   # 룰렛 돌아가는 중
        self.roulette_timer    = 0       # 현재 프레임
        self.roulette_duration = 180     # 총 프레임 (3초)
        self.roulette_idx      = 0       # 현재 강조 인덱스 (0~5)
        self.roulette_result   = None    # 최종 결과 챕터 ID
        self.roulette_flash    = 0       # 결과 플래시 타이머

        # ── 설정 창 ─────────────────────────────────────
        self.settings_open     = False
        self.settings_sel      = 0       # 현재 선택 항목 인덱스

        self.chapters = {
            "1": Chapter(
                "Orbital Void", "SHIP", -0.02,
                [(0.0,(10,20,30)),(0.4,(5,30,60)),(0.7,(30,10,50)),(1.0,(60,5,20))],
                90, "Zero-G 전투 · 기본 챕터 · SPACE 대쉬  [F] 변형",
                enemy_set="normal",
            ),
            "2": Chapter(
                "Corrupted City", "HUMAN", -0.25,
                [(0.0,(30,30,40)),(0.3,(40,25,35)),(0.6,(20,20,50)),(1.0,(50,10,10))],
                90, "폐허 도시 · 보병 작전 · 구조물 많음",
                enemy_set="normal",
            ),
            "3": Chapter(
                "Toxic Abyss", "SHIP", -0.18,
                [(0.0,(5,30,40)),(0.3,(0,50,60)),(0.6,(0,30,80)),(1.0,(0,10,60))],
                120, "심해 우주 · 심해함 전용 맵 · 독성 유체",
                enemy_set="abyss", special=["toxic_fluid","abyss_enemies","deep_gravity"],
            ),
            "4": Chapter(
                "Void Rift", "SHIP", -0.05,
                [(0.0,(20,0,40)),(0.3,(40,0,60)),(0.6,(60,0,80)),(1.0,(80,0,100))],
                120, "공허 균열 · 차원 적 전용 · 블랙홀 빈번",
                enemy_set="void", special=["frequent_blackhole","void_enemies"],
            ),
            "5": Chapter(
                "Gravity Well", "SHIP", -0.05,
                [(0.0,(40,10,20)),(0.3,(60,5,5)),(0.6,(10,10,60)),(1.0,(5,40,50))],
                150, "중력 웰 · 극강 난이도 · 모든 적 등장",
                enemy_set="all",
            ),
            "6": Chapter(
                "Abyss Sovereign", "SHIP", -0.03,
                [(0.0,(0,10,30)),(0.3,(0,5,50)),(0.7,(20,0,60)),(1.0,(40,0,80))],
                180, "최종 챕터 · 심연의 군주 · 블랙홀 지옥",
                enemy_set="all", special=["frequent_blackhole","void_enemies","abyss_enemies","mega_bosses"],
            ),
        }
        self.current_chapter = None

        self.enemies           = pygame.sprite.Group()
        self.projectiles       = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.gems              = pygame.sprite.Group()
        self.structures        = pygame.sprite.Group()
        self.fluids            = pygame.sprite.Group()
        self.companions        = pygame.sprite.Group()
        self.items             = pygame.sprite.Group()
        self.player            = None

        self.game_time   = 0
        self.spawn_timer = 0
        self.mouse_pos   = (400,300)
        self.notify_text  = ""
        self.notify_timer = 0
        self.levelup_choices = []
        self.levelup_active  = False
        self.particles = []
        self.star_field = StarField(180)
        self.high_score = 0
        self.shake_timer  = 0
        self.shake_amount = 0
        self.item_timer   = 0

    # ─────────────────────────────────────
    def start_game(self, chapter_id):
        # 색상 선택 화면 먼저
        self.pending_chapter_id  = chapter_id
        self.color_select_active = True
        self.color_select_idx    = 0
        self.state = "COLOR_SELECT"

    def _do_start_game(self, chapter_id):
        ch = self.chapters[chapter_id]
        self.current_chapter = ch
        self.player = Player((0,0))
        self.player.mode = ch.mode
        self.player.set_dimension("PHYSICAL")
        # 색상 선택 적용
        self.player.ship_color_key = SHIP_COLORS[self.color_select_idx]["key"]
        self.dimension = "PHYSICAL"
        self.camera_offset = Vector2(-400,-300)
        self.abyss_active = False
        self.abyss_timer  = 0
        self.blackholes   = []
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

        for g in [self.enemies, self.projectiles, self.enemy_projectiles,
                  self.gems, self.structures, self.fluids, self.companions, self.items]:
            g.empty()
        self.particles.clear()

        # 심해 챕터 — 심해함 기본 지급
        if "abyss" in ch.enemy_set or "3" == chapter_id:
            if "abyss_ship" not in self.player.unlocked_forms:
                self.player.unlocked_forms.append("abyss_ship")
            self.player.morph_to("abyss_ship")

        # 월드 구조물 배치
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
        self.notify("WASD 이동  SPACE 대쉬  SHIFT 차원전환  F 변형", 220)

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

    def _burst(self, world_pos, color, count=12, speed=4, life=30):
        for _ in range(count):
            a   = random.uniform(0,360)
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
            self.blackholes.append(bh)
            self.bh_spawn_cd = 600
            self.notify("⚫ 블랙홀 발생!", 120)
            self.screen_shake(8, 10)
            self._burst(pos, (180,0,255), count=30, speed=8, life=50)

    def _update_blackholes(self):
        # 흡입 트랜지션 처리 중이면 일반 업데이트 스킵
        if self.bh_suck_timer > 0:
            self.bh_suck_timer -= 1
            if self.bh_suck_timer == 30:
                self.bh_flash_timer = 25  # 화이트 플래시 시작
            if self.bh_suck_timer == 0:
                self._enter_rift()
            return

        for bh in self.blackholes[:]:
            bh.update()
            # 블랙홀 인력 — 플레이어
            pull = bh.apply_pull(self.player.world_pos, self.player.vel)
            self.player.vel += pull
            # 블랙홀 인력 — 적
            for enemy in self.enemies:
                p = bh.apply_pull(enemy.world_pos, enemy.vel)
                enemy.world_pos += p * 2
            # 블랙홀 안으로 들어온 적/탄 흡수
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

            # ── 플레이어가 블랙홀 코어에 흡입됨 ──
            player_d = (bh.world_pos - self.player.world_pos).length()
            if player_d < bh.radius * 0.6 and not self.rift_active and self.bh_suck_timer == 0:
                self.bh_suck_timer  = 60   # 1초 트랜지션
                self.bh_suck_target = bh
                self.rift_player_hp_save  = self.player.health
                self.rift_player_pos_save = Vector2(self.player.world_pos)
                self.screen_shake(20, 30)
                self._burst(self.player.world_pos, (200,0,255), count=40, speed=10, life=60)
                self.notify("⚫ 블랙홀에 흡입됨! 제3차원으로...", 100)
                return

            # 블랙홀 소멸 → 심해 차원 활성
            if not bh.alive:
                self.blackholes.remove(bh)
                self._activate_abyss(bh.world_pos)

        # ABYSS 차원 타이머
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
        """블랙홀 소멸 후 1분간 심해 차원 활성화"""
        self.abyss_active = True
        self.abyss_timer  = self.ABYSS_DURATION
        self.notify("⚠ 심해 차원 개방! 60초", 200)
        self.screen_shake(15, 20)
        self._burst(center_pos, (0,200,255), count=50, speed=10, life=80)
        # 심해 적 대량 소환
        for _ in range(8):
            angle = random.uniform(0,360)
            dist  = random.uniform(200,450)
            sp    = center_pos + Vector2(math.cos(math.radians(angle))*dist,
                                          math.sin(math.radians(angle))*dist)
            etype = random.choice(["abyss_eel","depth_guardian","leviathan_eye"])
            self.enemies.add(Enemy(sp, "PHYSICAL", etype, self.difficulty+1))
        # 아이템 드롭
        self._drop_item_at(center_pos, "shield")
        self._drop_item_at(center_pos + Vector2(50,0), "hp")

    # ─────────────────────────────────────
    #  RIFT DIMENSION (제3차원)
    # ─────────────────────────────────────
    def _enter_rift(self):
        """블랙홀 흡입 → 제3차원 진입"""
        self.rift_active = True
        self.rift_timer  = 0
        self.rift_enemies.empty()
        self.rift_projectiles.empty()
        self.rift_ep.empty()
        self.rift_particles.clear()

        # ── 처치 횟수에 따라 보스 선택 및 강화 ──────────
        RIFT_BOSS_POOL = [
            "rift_guardian",
            "rift_devourer",
            "void_wraith_king",
            "rift_colossus",
            "entropy_core",
            "abyss_rift_lord",
        ]
        k = self.rift_boss_kill_count
        # 처치 횟수에 따라 점점 강한 보스 등장 (순환)
        boss_idx  = k % len(RIFT_BOSS_POOL)
        boss_type = RIFT_BOSS_POOL[boss_idx]

        # 누적 강화 배율: 처치할 때마다 HP·속도 상승
        scale_mult = 1.0 + k * 0.35   # k=0→×1.0, k=1→×1.35, k=2→×1.70 …

        # 보스 생성 후 능력치 직접 보정
        boss_pos = Vector2(0, -200)
        boss_diff = self.difficulty + 1 + k * 0.5
        self.rift_boss = Enemy(boss_pos, "PHYSICAL", boss_type, boss_diff)
        # HP 스케일
        self.rift_boss.hp     = int(self.rift_boss.max_hp * scale_mult)
        self.rift_boss.max_hp = self.rift_boss.hp
        # 속도 스케일 (최대 3배까지)
        self.rift_boss.speed  = min(self.rift_boss.speed * (1 + k * 0.15), self.rift_boss.speed * 3)
        self.rift_enemies.add(self.rift_boss)

        # 주변 잡몹 수도 kill count에 따라 증가 (최대 8마리)
        minion_count = min(4 + k, 8)
        minion_pool  = ["null_fragment","void_titan","echo_phantom",
                        "glitcher","shadow_lurker","abyss_eel"]
        for i in range(minion_count):
            a  = i * (360 // minion_count)
            sp = Vector2(math.cos(math.radians(a))*250, math.sin(math.radians(a))*250)
            mtype = random.choice(minion_pool)
            self.rift_enemies.add(Enemy(sp, "PHYSICAL", mtype,
                                        self.difficulty + k * 0.3))

        # 플레이어 위치 리셋 (제3차원 중앙)
        self.player.world_pos = Vector2(0, 0)
        self.player.vel       = Vector2(0, 0)
        self.camera_offset    = Vector2(-400, -300)
        self.bh_flash_timer   = 40

        boss_name = ENEMY_DATA[boss_type]["name"]
        if k == 0:
            msg = f"⚡ 제3차원 돌입! {boss_name}를 처치하라!"
        else:
            msg = f"⚡ 제3차원! 강화된 {boss_name} (×{scale_mult:.1f})!"
        self.notify(msg, 240)
        self.screen_shake(18, 25)

    def _update_rift(self, keys, events):
        """제3차원 업데이트 루프"""
        self.rift_timer += 1

        # 플레이어 이동
        friction = -0.18
        self.player.update(keys, friction, self.current_chapter.mode, self.mouse_pos)
        self._update_camera()

        # 자동 사격
        self.player.timer += 1
        if self.player.timer > self.player.weapon_cooldown:
            self.player.timer = 0
            self._rift_auto_shoot()

        # 이벤트 처리 (마우스 클릭 수동 사격)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._rift_manual_shoot(event.pos)

        # 적 업데이트
        rift_list = list(self.rift_enemies)
        for enemy in rift_list:
            enemy.update(self.player.world_pos,
                         enemy_projectiles=self.rift_ep,
                         dimension="PHYSICAL",
                         all_enemies=rift_list)

        # 플레이어 탄 vs 적
        for p in list(self.rift_projectiles):
            p.update()
            p_r = pygame.Rect(p.world_pos.x-6, p.world_pos.y-6, 12,12)
            for enemy in list(self.rift_enemies):
                er = pygame.Rect(enemy.world_pos.x-enemy.rect.w//2,
                                 enemy.world_pos.y-enemy.rect.h//2,
                                 enemy.rect.w, enemy.rect.h)
                if er.colliderect(p_r):
                    dmg = int(p.dmg * self.player.get_dmg_mult())
                    if enemy.take_damage(dmg):
                        self._rift_burst(enemy.world_pos, (200,50,255), count=18)
                        if enemy is self.rift_boss:
                            self.rift_boss = None
                        enemy.kill()
                        self.player.score += 500
                    if enemy.special != "phase_boss":
                        p.kill()
                    break

        # 적 탄 업데이트 & 피격
        player_wr = pygame.Rect(self.player.world_pos.x-14, self.player.world_pos.y-14, 28,28)
        for ep in list(self.rift_ep):
            ep.update()
            ep_r = pygame.Rect(ep.world_pos.x-7, ep.world_pos.y-7, 14,14)
            if ep_r.colliderect(player_wr) and self.player.invincible <= 0:
                actual = self.player.take_hit(ep.dmg)
                self.screen_shake(5,6)
                ep.kill()
                if self.player.health <= 0:
                    self.state = "DEATH"
                    self.high_score = max(self.high_score, self.player.score)
                    return

        # 접촉 데미지
        if self.player.invincible <= 0:
            for enemy in list(self.rift_enemies):
                er = pygame.Rect(enemy.world_pos.x-enemy.rect.w//2,
                                 enemy.world_pos.y-enemy.rect.h//2,
                                 enemy.rect.w, enemy.rect.h)
                if er.colliderect(player_wr):
                    actual = self.player.take_hit(15)
                    self.screen_shake(6,8)
                    if self.player.health <= 0:
                        self.state = "DEATH"
                        self.high_score = max(self.high_score, self.player.score)
                        return
        if self.player.invincible > 0:
            self.player.invincible -= 1

        # 파티클
        self.rift_particles = [p for p in self.rift_particles if p.update()]

        # 보스 처치 확인 → 탈출
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
        for _ in range(count):
            a   = random.uniform(0,360)
            spd = random.uniform(1, speed)
            vel = Vector2(math.cos(math.radians(a))*spd, math.sin(math.radians(a))*spd)
            self.rift_particles.append(Particle(world_pos, vel, color,
                                                life+random.randint(-5,5), random.randint(2,5)))

    def _exit_rift(self):
        """제3차원 탈출 → 원래 차원 복귀"""
        self.rift_active = False
        self.player.world_pos = Vector2(self.rift_player_pos_save)
        self.player.vel       = Vector2(0,0)
        self.camera_offset    = self.player.world_pos - Vector2(400, 300)
        # 블랙홀 제거 (흡입한 블랙홀)
        if self.bh_suck_target in self.blackholes:
            self.blackholes.remove(self.bh_suck_target)
        self.bh_suck_target = None

        # ── 균열 보스 처치 카운트 증가 및 보상 ──────────
        self.rift_boss_kill_count += 1
        k = self.rift_boss_kill_count
        bonus_score = 500 + (k - 1) * 300
        self.player.score += bonus_score
        # HP 회복 (처치 수 많을수록 조금 줄어듦, 최소 20)
        hp_bonus = max(20, 50 - (k - 1) * 5)
        self.player.health = min(self.player.max_health,
                                 self.player.health + hp_bonus)
        # 매 3회마다 사격 속도 보너스
        extra = ""
        if k % 3 == 0:
            self.player._cd_bonus += 1
            extra = "  사격속도 +1!"

        self.bh_flash_timer = 35
        self.screen_shake(15, 20)
        self._burst(self.player.world_pos, (100,255,200), count=50, speed=9, life=70)
        self.notify(
            f"✨ 제3차원 탈출! HP+{hp_bonus}  SCORE+{bonus_score}"
            f"  [보스처치:{k}회]{extra}", 280)



    # ─────────────────────────────────────
    #  DIMENSION SHIFT → blackhole chance
    # ─────────────────────────────────────
    def _on_dimension_shift(self):
        prob = 0.30 if "frequent_blackhole" in self.current_chapter.special else 0.15
        if random.random() < prob:
            self._force_spawn_blackhole()

    def _force_spawn_blackhole(self):
        if len(self.blackholes) >= 4:
            return
        angle = random.uniform(0,360)
        dist  = random.uniform(150, 350)
        pos   = self.player.world_pos + Vector2(
            math.cos(math.radians(angle))*dist,
            math.sin(math.radians(angle))*dist)
        bh = Blackhole(pos)
        self.blackholes.append(bh)
        self.notify("⚫ 차원 충격! 블랙홀 발생!", 130)
        self.screen_shake(10, 12)
        self._burst(pos, (200,50,255), count=20, speed=7, life=45)

    # ─────────────────────────────────────
    #  UPDATE
    # ─────────────────────────────────────
    def update(self, events):
        self.mouse_pos = pygame.mouse.get_pos()
        if self.notify_timer > 0: self.notify_timer -= 1
        if self.shake_timer   > 0: self.shake_timer   -= 1
        if self.bh_flash_timer > 0: self.bh_flash_timer -= 1
        if self.roulette_flash > 0: self.roulette_flash -= 1

        # ── 설정 창 전역 처리 ────────────────────────────
        if self.settings_open:
            for event in events:
                self._handle_settings_input(event)
            return

        # ── 룰렛 진행 ───────────────────────────────────
        if self.roulette_active and self.state == "MENU":
            self.roulette_timer += 1
            t = self.roulette_timer / self.roulette_duration  # 0→1
            # 감속 곡선: easeOut — 초반 빠르게, 후반 느리게
            speed = max(1, int(7 - t * 6.2))
            if self.roulette_timer % speed == 0:
                self.roulette_idx = (self.roulette_idx + 1) % 6
            if self.roulette_timer >= self.roulette_duration:
                # 마지막에 target 위치로 snap
                target = getattr(self, '_roulette_target', random.randint(0, 5))
                self.roulette_idx    = target
                self.roulette_active = False
                self.roulette_result = str(target + 1)
                self.roulette_flash  = 150
            return

        # 색상 선택 화면
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
            return

        # 제3차원 전투
        if self.rift_active:
            keys = pygame.key.get_pressed()
            self._update_rift(keys, events)
            return

        # 변형 선택 UI
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

        # 레벨업
        if self.levelup_active:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1 and len(self.levelup_choices)>=1: self._apply_levelup_choice(0)
                    elif event.key == pygame.K_2 and len(self.levelup_choices)>=2: self._apply_levelup_choice(1)
                    elif event.key == pygame.K_3 and len(self.levelup_choices)>=3: self._apply_levelup_choice(2)
            return

        if self.state != "PLAYING":
            if self.state == "MENU":
                self.game_time += 1   # 메뉴 룰렛 애니메이션용 타이머
            return

        keys = pygame.key.get_pressed()
        self.game_time += 1
        progress = min(1.0, self.game_time / (self.current_chapter.duration * 60))
        self.difficulty = 1.0 + progress * 4.5

        for event in events:
            if event.type == pygame.KEYDOWN:
                # 설정 창 토글 (ESC 또는 TAB)
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_TAB:
                    self.settings_open = not self.settings_open
                    self.settings_sel  = 0

            if self.settings_open:
                self._handle_settings_input(event)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: self._manual_shoot(event.pos)
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
                    self._on_dimension_shift()   # ← 블랙홀 확률 발생
                elif event.key == pygame.K_q:
                    self.player.switch_weapon(-1)
                    self.notify(f"무기: {self.player.weapon['name']}", 80)
                elif event.key == pygame.K_e:
                    self.player.switch_weapon(1)
                    self.notify(f"무기: {self.player.weapon['name']}", 80)
                elif event.key == pygame.K_SPACE:
                    if self.player.try_dash(keys):
                        self._burst(self.player.world_pos, (255,255,255), count=8, speed=5, life=15)
                elif event.key == pygame.K_f and self.player.mode == "SHIP":
                    if len(self.player.unlocked_forms) > 1:
                        self.form_select_active = True
                        self.form_select_idx = self.player.unlocked_forms.index(self.player.ship_form)
                    else:
                        self.notify("해금된 변형 없음. 레벨업 시 획득!", 100)

        # 물리
        if self.settings_open:
            return   # 설정 창 열린 동안은 게임 일시정지

        friction = self.current_chapter.friction
        buoyancy = 0
        for f in self.fluids:
            if f.get_world_rect().collidepoint(self.player.world_pos.x, self.player.world_pos.y):
                friction *= 2; buoyancy = f.buoyancy
        # 심해 중력 특수
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

        # 적 소환
        self.spawn_timer += 1
        interval = max(3, int(35 - self.difficulty * 3))
        if self.spawn_timer > interval:
            self.spawn_timer = 0
            self._spawn_enemy(progress)

        # 아이템 타이머
        self.item_timer += 1
        if self.item_timer > 600:
            self.item_timer = 0
            self._drop_random_item()

        # 자동사격
        self.player.timer += 1
        if self.player.timer > self.player.weapon_cooldown:
            self.player.timer = 0
            self._auto_shoot()

        # 동반자
        for comp in self.companions:
            comp.update(self.enemies, self.projectiles, self.dimension, self.camera_offset)

        # 투사체 이동
        for p in list(self.projectiles):
            p.update()
        for ep in list(self.enemy_projectiles):
            ep.update()

        # 적 이동
        enemy_list = list(self.enemies)
        for enemy in enemy_list:
            if enemy.dimension_type == self.dimension or self.abyss_active:
                enemy.update(self.player.world_pos,
                             enemy_projectiles=self.enemy_projectiles,
                             dimension=self.dimension,
                             all_enemies=enemy_list)

        # 플레이어 접촉 데미지
        player_wr2 = pygame.Rect(self.player.world_pos.x-14, self.player.world_pos.y-14, 28,28)
        if self.player.invincible <= 0:
            for enemy in list(self.enemies):
                if enemy.dimension_type == self.dimension or self.abyss_active:
                    er = pygame.Rect(enemy.world_pos.x-enemy.rect.w//2,
                                     enemy.world_pos.y-enemy.rect.h//2,
                                     enemy.rect.w, enemy.rect.h)
                    if er.colliderect(player_wr2):
                        dmg = 20 if enemy.max_hp >= 100 else (10 if enemy.max_hp >= 20 else 5)
                        actual = self.player.take_hit(dmg)
                        self.screen_shake(6,8)
                        self.notify(f"피격! HP -{actual}" if actual>0 else "쉴드 흡수!", 50)
                        if self.player.health <= 0:
                            self.state = "DEATH"
                            self.high_score = max(self.high_score, self.player.score)
                            return
        if self.player.invincible > 0:
            self.player.invincible -= 1

        # 적 투사체 vs 플레이어
        for ep in list(self.enemy_projectiles):
            if ep.dimension == self.dimension or self.abyss_active:
                ep_r = pygame.Rect(ep.world_pos.x-7, ep.world_pos.y-7, 14,14)
                if ep_r.colliderect(player_wr2) and self.player.invincible <= 0:
                    actual = self.player.take_hit(ep.dmg)
                    self.screen_shake(5,6)
                    self.notify(f"피격! HP -{actual}" if actual>0 else "쉴드 흡수!", 50)
                    ep.kill()
                    if self.player.health <= 0:
                        self.state = "DEATH"
                        self.high_score = max(self.high_score, self.player.score)
                        return

        # 플레이어 탄 vs 적
        for p in list(self.projectiles):
            p_r = pygame.Rect(p.world_pos.x-6, p.world_pos.y-6, 12,12)
            for enemy in list(self.enemies):
                if enemy.dimension_type == p.dimension or self.abyss_active:
                    er = pygame.Rect(enemy.world_pos.x-enemy.rect.w//2,
                                     enemy.world_pos.y-enemy.rect.h//2,
                                     enemy.rect.w, enemy.rect.h)
                    if er.colliderect(p_r):
                        dmg = int(p.dmg * self.player.get_dmg_mult())
                        if enemy.take_damage(dmg):
                            data = ENEMY_DATA.get(enemy.etype, {})
                            col  = data.get("cp",(255,100,0)) if self.dimension=="PHYSICAL" else data.get("cv",(255,0,200))
                            self._burst(enemy.world_pos, col, count=15, speed=5, life=35)
                            if enemy.max_hp >= 20: self.screen_shake(10,12)
                            self.gems.add(Gem(enemy.world_pos, enemy.gem_val))
                            if random.random() < 0.10: self._drop_item_at(enemy.world_pos)
                            combo = self.player.kill_combo()
                            mult  = self.player.get_combo_multiplier()
                            pts   = int(enemy.gem_val * 10 * mult)
                            self.player.score += pts
                            if combo % 5 == 0 and combo >= 5:
                                self.notify(f"COMBO ×{combo}!  ×{mult:.1f}", 90)
                            enemy.kill()
                        if enemy.special != "phase_boss":
                            p.kill()
                        break

        # 젬 수집
        for gem in list(self.gems):
            gem.update()
            if (self.player.world_pos - gem.world_pos).length() < 32:
                self.player.xp += gem.value
                self._burst(gem.world_pos, (0,255,150), count=5, speed=3, life=18)
                if self.player.xp >= self.player.xp_to_next:
                    self._trigger_levelup()
                gem.kill()

        # 아이템 수집
        for item in list(self.items):
            if not item.update():
                item.kill(); continue
            if (self.player.world_pos - item.world_pos).length() < 26:
                self._apply_item(item.itype)
                self._burst(item.world_pos, ITEM_DATA.get(item.itype,{"color":(255,255,255)})["color"], count=10)
                item.kill()

        self.particles = [p for p in self.particles if p.update()]

        if self.game_time > self.current_chapter.duration * 60:
            # ── 최종 보스가 살아있는 동안은 절대 끝나지 않음 ──────────────
            final_bosses = ["void_god","abyss_sovereign","nexus_overmind","abyssal_tyrant"]
            alive_finals = [e for e in self.enemies if e.etype in final_bosses]
            if alive_finals:
                # 보스 살아있으면 game_time 동결 (difficulty 중복 증가 방지)
                self.game_time = self.current_chapter.duration * 60
                # notify_timer가 0일 때만 알림 (스팸 방지)
                if self.notify_timer <= 0:
                    boss_name = alive_finals[0].name
                    self.notify(f"★ {boss_name}를 처치해야 클리어! ★", 240)
                return
            # ── 최종 보스 강제 소환 (한 번만) ────────────────────────────
            if "mega_bosses" in self.current_chapter.special:
                for fb in ["void_god","abyss_sovereign"]:
                    if not any(e.etype == fb for e in self.enemies):
                        angle = random.uniform(0,360)
                        sp = self.player.world_pos + Vector2(
                            math.cos(math.radians(angle))*400,
                            math.sin(math.radians(angle))*400)
                        self.difficulty += 1.0
                        self.enemies.add(Enemy(sp, "PHYSICAL", fb, self.difficulty))
                        self.notify(f"★★ {ENEMY_DATA[fb]['name']} 강제 출현! 처치하라! ★★", 300)
                        self.screen_shake(25, 30)
                        self.game_time = self.current_chapter.duration * 60
                        return
            else:
                # 일반 챕터 — nexus/abyssal 둘 다 체크
                general_final = ["nexus_overmind","abyssal_tyrant"]
                for fb in general_final:
                    if not any(e.etype == fb for e in self.enemies):
                        angle = random.uniform(0,360)
                        sp = self.player.world_pos + Vector2(
                            math.cos(math.radians(angle))*400,
                            math.sin(math.radians(angle))*400)
                        self.difficulty += 1.0
                        self.enemies.add(Enemy(sp, "PHYSICAL", fb, self.difficulty))
                        self.notify(f"⚠ {ENEMY_DATA[fb]['name']} 최후의 저항! 처치해야 클리어!", 300)
                        self.screen_shake(20, 25)
                        self.game_time = self.current_chapter.duration * 60
                        return
            # 모든 최종보스 처치 완료 → 진짜 클리어
            self.high_score = max(self.high_score, self.player.score)
            self.state = "WIN"

    # ─────────────────────────────────────
    #  SETTINGS WINDOW
    # ─────────────────────────────────────
    def _handle_settings_input(self, event):
        """설정 창이 열려있을 때 입력 처리"""
        if event.type != pygame.KEYDOWN:
            return
        keys_order = SETTINGS.KEYS_ORDER
        n = len(keys_order)

        if event.key in (pygame.K_ESCAPE, pygame.K_TAB):
            self.settings_open = False
            return
        elif event.key == pygame.K_UP:
            self.settings_sel = (self.settings_sel - 1) % (n + 1)  # +1 for reset row
        elif event.key == pygame.K_DOWN:
            self.settings_sel = (self.settings_sel + 1) % (n + 1)
        elif self.settings_sel < n:
            # 값 조정
            key = keys_order[self.settings_sel]
            label, vmin, vmax, step = SETTINGS.LABELS[key]
            cur = getattr(SETTINGS, key)
            if event.key == pygame.K_LEFT:
                new_val = round(max(vmin, cur - step), 4)
                setattr(SETTINGS, key, new_val)
            elif event.key == pygame.K_RIGHT:
                new_val = round(min(vmax, cur + step), 4)
                setattr(SETTINGS, key, new_val)
        elif self.settings_sel == n:
            # 리셋 버튼
            if event.key == pygame.K_RETURN:
                SETTINGS.reset_defaults()
                self.notify("설정 초기화 완료!", 90)

    def _draw_settings(self):
        """인게임 설정 오버레이 렌더링"""
        ov = pygame.Surface((800, 600), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        self.screen.blit(ov, (0, 0))

        # 타이틀
        self.draw_text("⚙  게임 설정", (400, 32), 34, (0, 220, 255))
        self.draw_text("↑↓ 항목 이동   ←→ 값 조정   ESC/TAB 닫기   ENTER 리셋(하단)", (400, 62), 14, (140, 160, 200))

        keys_order = SETTINGS.KEYS_ORDER
        n = len(keys_order)

        # 섹션 구분선 위치
        sections = {
            0: "── SHIP 이동 ──────────────────────",
            4: "── HUMAN 이동 ─────────────────────",
            6: "── 대쉬 ────────────────────────────",
            9: "── 카메라 ──────────────────────────",
        }

        row_h = 42
        start_y = 90

        for i, key in enumerate(keys_order):
            y = start_y + i * row_h

            # 섹션 헤더
            if i in sections:
                self.draw_text(sections[i], (400, y - 10), 12, (70, 90, 120))
                y += 8

            label, vmin, vmax, step = SETTINGS.LABELS[key]
            cur = getattr(SETTINGS, key)
            sel = (i == self.settings_sel)

            # 배경 카드
            card_col  = (30, 50, 80)  if sel else (15, 20, 35)
            border_col = (0, 200, 255) if sel else (40, 50, 70)
            pygame.draw.rect(self.screen, card_col,  (60, y, 680, 32), border_radius=6)
            pygame.draw.rect(self.screen, border_col, (60, y, 680, 32), 2 if sel else 1, border_radius=6)

            # 라벨
            self.draw_text(label, (200, y + 16), 16, (255, 230, 100) if sel else (180, 190, 210))

            # 슬라이더 바
            bar_x, bar_y, bar_w, bar_h = 360, y + 11, 260, 10
            pygame.draw.rect(self.screen, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            t = (cur - vmin) / max(vmax - vmin, 0.0001)
            fill_w = max(6, int(bar_w * t))
            fill_col = (0, 200, 255) if sel else (0, 130, 180)
            pygame.draw.rect(self.screen, fill_col, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
            # 슬라이더 핸들
            hx = bar_x + fill_w
            pygame.draw.circle(self.screen, (255, 255, 255) if sel else (150, 200, 220), (hx, bar_y + 5), 6 if sel else 4)

            # 수치 표시
            if isinstance(step, float):
                val_str = f"{cur:.2f}"
            else:
                val_str = str(int(cur))
            self.draw_text(val_str, (670, y + 16), 16, (255, 255, 200) if sel else (160, 170, 180))

            # 최소/최대 힌트
            if sel:
                if isinstance(step, float):
                    self.draw_text(f"[{vmin:.2f}~{vmax:.2f}  step:{step}]", (400, y + 34), 11, (90, 120, 160))

        # 리셋 버튼 행
        reset_y = start_y + n * row_h + 6
        sel_reset = (self.settings_sel == n)
        rc = (60, 20, 20) if sel_reset else (25, 15, 15)
        bc = (255, 80, 80) if sel_reset else (80, 40, 40)
        pygame.draw.rect(self.screen, rc, (200, reset_y, 400, 32), border_radius=8)
        pygame.draw.rect(self.screen, bc, (200, reset_y, 400, 32), 2, border_radius=8)
        self.draw_text("[ ENTER ] — 모든 설정 초기화", (400, reset_y + 16), 17,
                       (255, 120, 120) if sel_reset else (160, 80, 80))

    # ─────────────────────────────────────
    def _drop_item_at(self, world_pos, forced=None):
        if forced:
            self.items.add(PickupItem(world_pos, forced))
            return
        itype = random.choices(
            ["hp","shield","speed","ammo","ship_form"],
            weights=[0.35, 0.25, 0.20, 0.10, 0.10])[0]
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
            # 랜덤 변형 해금
            locked = [k for k in SHIP_FORMS if k not in self.player.unlocked_forms]
            if locked:
                f = random.choice(locked)
                self.player.unlocked_forms.append(f)
                self.notify(f"변형 해금: {SHIP_FORMS[f]['name']}! [F]로 변경", 180)
            else:
                self.player._cd_bonus += 1
                self.notify("사격 속도 +1! (모든 변형 해금)", 100)

    # ─────────────────────────────────────
    def _spawn_enemy(self, progress):
        angle = random.uniform(0,360)
        dist  = random.uniform(420,620)
        sp    = self.player.world_pos + Vector2(math.cos(math.radians(angle)),
                                                 math.sin(math.radians(angle))) * dist
        dim = random.choice(["PHYSICAL","VOID"])
        ch  = self.current_chapter

        # 최종 보스
        if "mega_bosses" in ch.special:
            mega = ["void_god","abyss_sovereign"]
            for mb in mega:
                bp = ENEMY_DATA[mb]["spawn_progress"]
                if progress >= bp and not any(e.etype==mb for e in self.enemies):
                    self.enemies.add(Enemy(sp, dim, mb, self.difficulty))
                    self.notify(f"★★ {ENEMY_DATA[mb]['name']} 출현! ★★", 250)
                    self.screen_shake(20,25)
                    return

        boss_types = ["nexus_overmind","abyssal_tyrant"]
        for bt in boss_types:
            bp = ENEMY_DATA[bt]["spawn_progress"]
            if progress >= bp and not any(e.etype==bt for e in self.enemies):
                self.enemies.add(Enemy(sp, dim, bt, self.difficulty))
                self.notify(f"⚠ {ENEMY_DATA[bt]['name']} 출현!", 200)
                self.screen_shake(15,20); return

        mid_bosses = [("echo_wraith",0.70),("dreadnought_construct",0.50),("anomaly_core",0.25)]
        if ch.enemy_set == "abyss":
            mid_bosses = [("abyss_leviathan",0.55),("anomaly_core",0.25)]
        elif ch.enemy_set == "void":
            mid_bosses = [("null_colossus",0.60),("echo_wraith",0.40)]
        for mbt, mp in mid_bosses:
            if progress >= mp and not any(e.etype==mbt for e in self.enemies):
                self.enemies.add(Enemy(sp, dim, mbt, self.difficulty))
                self.notify(f"⚡ {ENEMY_DATA[mbt]['name']} 등장!", 160)
                self.screen_shake(10,12); return

        # 일반 적 — 챕터별 풀
        abyss_pool = ["abyss_eel","depth_guardian","leviathan_eye","basic_drone"]
        void_pool  = ["null_fragment","void_titan","echo_phantom","glitcher"]
        normal_pool = ["basic_drone","swarm_organism","glitcher","hunter_drone",
                       "sentinel","sniper_node","elite_enforcer","void_weaver",
                       "corrupted_sentry","shadow_lurker"]

        if ch.enemy_set == "abyss":
            pool = abyss_pool
        elif ch.enemy_set == "void":
            pool = void_pool
        elif ch.enemy_set == "all":
            pool = normal_pool + abyss_pool + void_pool
        else:
            pool = normal_pool

        r = random.random()
        if progress > 0.7 and r < 0.12:
            etype = random.choice([p for p in pool if ENEMY_DATA.get(p,{}).get("hp",1)>=3])
        elif progress > 0.5 and r < 0.22:
            etype = random.choice(pool[len(pool)//2:] or pool)
        elif r < 0.38:
            # 군집 5마리
            sw = "swarm_organism" if ch.enemy_set not in ("abyss","void") else pool[0]
            for _ in range(5):
                off = Vector2(random.uniform(-45,45), random.uniform(-45,45))
                self.enemies.add(Enemy(sp+off, dim, sw, self.difficulty))
            return
        else:
            etype = random.choice(pool)

        self.enemies.add(Enemy(sp, dim, etype, self.difficulty))

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
                                            color_override=col, speed=w["speed"],
                                            dmg=w["dmg"], is_direction=True, size=w["size"]))

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
        if locked_f:
            choices.append(("form", locked_f[0]))
        if locked_w:
            choices.append(("weapon", locked_w[0]))
        choices.append(("stat","cooldown"))
        choices.append(("stat","maxhp"))
        choices.append(("stat","robot"))
        random.shuffle(choices)
        self.levelup_choices = choices[:3]
        self.levelup_active  = True

    def _apply_levelup_choice(self, idx):
        if idx >= len(self.levelup_choices): return
        ctype, cval = self.levelup_choices[idx]
        if ctype == "weapon":
            self.player.unlocked_weapons.append(cval)
            self.player.weapon_key = cval
            self.notify(f"무기 해금: {WEAPONS[cval]['name']}!", 150)
        elif ctype == "form":
            self.player.unlocked_forms.append(cval)
            self.notify(f"변형 해금: {SHIP_FORMS[cval]['name']}! [F]로 변경", 160)
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
                if not any(isinstance(c, RobotCompanion) for c in self.companions):
                    self.companions.add(RobotCompanion(self.player))
                    self.notify("로봇 동반자 소환!", 150)
                else:
                    self.player._cd_bonus += 1
                    self.notify("사격 속도 +1!", 120)
        self.levelup_active = False

    # ─────────────────────────────────────
    #  DRAW
    # ─────────────────────────────────────
    def draw(self):
        shake = Vector2(0,0)
        if self.shake_timer > 0:
            shake = Vector2(random.uniform(-self.shake_amount, self.shake_amount),
                            random.uniform(-self.shake_amount, self.shake_amount))
        if self.state   == "MENU":
            self._draw_menu()
            if self.settings_open:
                self._draw_settings()
        elif self.state == "COLOR_SELECT": self._draw_color_select()
        elif self.state == "PLAYING":
            if self.rift_active:
                self._draw_rift(shake)
            else:
                self._draw_playing(shake)
            # 설정 창 (PLAYING 위에 오버레이)
            if self.settings_open:
                self._draw_settings()
        elif self.state == "DEATH":   self._draw_death()
        elif self.state == "WIN":     self._draw_win()
        pygame.display.flip()

    # ─────────────────────────────────────
    def _draw_menu(self):
        self.screen.fill((6,6,12))
        rng = random.Random(42)
        for _ in range(140):
            x=rng.randint(0,800); y=rng.randint(0,600); b=rng.randint(40,160)
            pygame.draw.circle(self.screen, (b,b,b+40), (x,y), 1)

        self.draw_text("ECHOES OF THE CONTINUUM", (400,48), 42, (0,220,255))
        self.draw_text("Infinite Dimension Survival", (400,92), 20, (80,180,255))
        self.draw_text("마우스 클릭 또는 숫자키 [1~6] 선택", (400,118), 16, (110,110,150))

        mx, my = pygame.mouse.get_pos()
        # ── 챕터 카드: 2열 3행 ──
        cols = 2
        card_w, card_h = 340, 88
        x_start = 60; y_start = 158; x_gap = 360; y_gap = 108
        chapter_list = list(self.chapters.items())
        for i, (cid, ch) in enumerate(chapter_list):
            row = i // cols; ci = i % cols
            cx  = x_start + ci * x_gap + card_w // 2
            cy  = y_start + row * y_gap + card_h // 2
            card = pygame.Rect(x_start + ci * x_gap, y_start + row * y_gap, card_w, card_h)
            hovered = card.collidepoint(mx,my)

            # 룰렛 강조
            is_roulette_hi = self.roulette_active and (self.roulette_idx == i)
            is_result      = (self.roulette_result == cid and self.roulette_flash > 0)

            if is_result:
                flash_t = self.roulette_flash / 150
                pulse   = int(40 + 40 * math.sin(self.roulette_flash * 0.25))
                bg_col  = (pulse, pulse//2, 0)
                bc      = (255, 220, 50)
                bw_line = 3
            elif is_roulette_hi:
                bg_col  = (50, 40, 10)
                bc      = (255, 180, 0)
                bw_line = 3
            elif hovered:
                bg_col = (35,35,60); bc = (255,255,100); bw_line = 2
            else:
                bg_col = (16,16,28)
                mode_col_base = (0,200,255) if ch.mode=="SHIP" else (0,255,150)
                bc = mode_col_base; bw_line = 1

            mode_col = (0,200,255) if ch.mode=="SHIP" else (0,255,150)
            pygame.draw.rect(self.screen, bg_col, card, border_radius=10)
            pygame.draw.rect(self.screen, bc, card, bw_line, border_radius=10)

            # 결과 카드에 별 반짝임
            if is_result:
                for si in range(6):
                    sa = (self.game_time * 4 + si * 60) % 360
                    sr = 50
                    spx = cx + int(math.cos(math.radians(sa)) * sr)
                    spy = cy + int(math.sin(math.radians(sa)) * sr)
                    pygame.draw.circle(self.screen, (255,220,50), (spx,spy), 3)

            name_col = (255,220,50) if is_result else mode_col
            self.draw_text(f"[{cid}] {ch.name}", (cx, cy - 22), 21, name_col)
            self.draw_text(ch.mode, (cx, cy + 1), 14, (150,150,180))
            ov = ch.overview[:36]
            self.draw_text(ov, (cx, cy + 22), 12, (130,130,160))

        # ── 룰렛 버튼 & 결과 영역 ──────────────────────
        self._draw_roulette_section(mx, my)

        if self.high_score > 0:
            self.draw_text(f"최고 점수: {self.high_score:,}", (400,578), 18, (255,220,80))
        self.draw_text("WASD이동  SPACE대쉬  SHIFT차원전환  F변형  Q/E무기전환", (400,557), 13, (70,70,110))

    def _draw_roulette_section(self, mx, my):
        """룰렛 버튼 + 슬롯머신 스타일 표시줄"""
        # ── 슬롯 표시줄 (6칸 가로 나열) ─────────────────
        slot_y    = 494
        slot_w    = 88
        slot_h    = 36
        slot_gap  = 6
        total_w   = 6 * slot_w + 5 * slot_gap
        slot_x0   = (800 - total_w) // 2

        chapter_list = list(self.chapters.items())

        for i, (cid, ch) in enumerate(chapter_list):
            sx = slot_x0 + i * (slot_w + slot_gap)
            slot_rect = pygame.Rect(sx, slot_y, slot_w, slot_h)

            is_hi     = self.roulette_active and (self.roulette_idx == i)
            is_result = (self.roulette_result == cid and self.roulette_flash > 0)

            if is_result:
                pulse = int(60 + 40 * math.sin(self.roulette_flash * 0.3))
                bg  = (pulse, pulse//2, 0)
                bc  = (255, 220, 50)
                bw  = 3
                tc  = (255, 255, 100)
            elif is_hi:
                bg  = (60, 50, 0)
                bc  = (255, 200, 0)
                bw  = 3
                tc  = (255, 220, 80)
            else:
                bg  = (20, 20, 35)
                bc  = (60, 60, 100)
                bw  = 1
                tc  = (100, 120, 160)

            pygame.draw.rect(self.screen, bg,  slot_rect, border_radius=6)
            pygame.draw.rect(self.screen, bc,  slot_rect, bw, border_radius=6)
            self.draw_text(f"{cid}", (sx + slot_w//2, slot_y + 10), 14, tc)
            self.draw_text(ch.name[:7], (sx + slot_w//2, slot_y + 26), 10, tc)

        # 선택 화살표 (현재 강조 위)
        if self.roulette_active:
            hi_x = slot_x0 + self.roulette_idx * (slot_w + slot_gap) + slot_w // 2
            arrow_pts = [(hi_x, slot_y - 4), (hi_x - 8, slot_y - 16), (hi_x + 8, slot_y - 16)]
            pygame.draw.polygon(self.screen, (255, 200, 0), arrow_pts)
        elif self.roulette_result:
            ri = int(self.roulette_result) - 1
            hi_x = slot_x0 + ri * (slot_w + slot_gap) + slot_w // 2
            col = (255, 220, 50) if self.roulette_flash > 0 else (120, 120, 60)
            arrow_pts = [(hi_x, slot_y - 4), (hi_x - 8, slot_y - 16), (hi_x + 8, slot_y - 16)]
            pygame.draw.polygon(self.screen, col, arrow_pts)

        # ── 룰렛 버튼 ────────────────────────────────────
        btn_rect = pygame.Rect(310, 536, 180, 36)
        btn_hov  = btn_rect.collidepoint(mx, my)
        if self.roulette_active:
            btn_col = (60, 60, 80); btn_bc = (80,80,100); btn_tc = (100,100,130)
            btn_txt = "돌아가는 중..."
        elif btn_hov:
            btn_col = (40, 30, 0); btn_bc = (255,200,0); btn_tc = (255,220,80)
            btn_txt = "🎰 ROULETTE [R]"
        else:
            btn_col = (20, 15, 0); btn_bc = (140,100,0); btn_tc = (200,160,50)
            btn_txt = "🎰 ROULETTE [R]"
        pygame.draw.rect(self.screen, btn_col, btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, btn_bc,  btn_rect, 2, border_radius=8)
        self.draw_text(btn_txt, (400, 554), 16, btn_tc)

        # ── 결과 출력 + 바로 시작 버튼 ───────────────────
        if self.roulette_result and self.roulette_flash > 0:
            rid  = self.roulette_result
            rch  = self.chapters[rid]
            # 결과 텍스트
            self.draw_text(
                f"★  챕터 {rid}: {rch.name}  ★",
                (400, 476), 20, (255, 230, 60))
            # 바로 시작 버튼
            go_rect = pygame.Rect(270, 576, 260, 34)
            go_hov  = go_rect.collidepoint(mx, my)
            go_bg   = (0, 60, 20) if go_hov else (0, 30, 10)
            go_bc   = (0, 255, 100) if go_hov else (0, 150, 60)
            pygame.draw.rect(self.screen, go_bg,  go_rect, border_radius=8)
            pygame.draw.rect(self.screen, go_bc,  go_rect, 2, border_radius=8)
            self.draw_text(f"▶  챕터 {rid} 바로 시작!", (400, 593), 16,
                           (0,255,100) if go_hov else (0,200,80))

    # ─────────────────────────────────────
    def _draw_color_select(self):
        """우주선 색상 선택 화면"""
        self.screen.fill((6,6,16))
        # 배경 별
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
            bx = x_start + ci * x_gap
            by = y_start + row * y_gap
            card = pygame.Rect(bx, by, card_w, card_h)
            sel  = (i == self.color_select_idx)
            hov  = card.collidepoint(mx, my)

            bg  = (40,30,65) if sel else ((28,28,48) if hov else (16,16,32))
            bc  = (255,230,50) if sel else ((150,150,200) if hov else (60,60,100))
            pygame.draw.rect(self.screen, bg, card, border_radius=10)
            pygame.draw.rect(self.screen, bc, card, 2 if sel else 1, border_radius=10)

            # 우주선 미리보기 (삼각형 폴리곤)
            cx_c = bx + card_w // 2
            cy_c = by + 52
            scale = 16
            poly = [(cx_c, cy_c - scale),
                    (cx_c + scale, cy_c + scale),
                    (cx_c - scale, cy_c + scale)]
            col_p = cd["color_p"]
            col_v = cd["color_v"]
            pygame.draw.polygon(self.screen, col_p, poly)
            pygame.draw.polygon(self.screen, (255,255,255), poly, 1)
            # VOID 색상 작게 옆에
            poly_v = [(cx_c+26, cy_c - 8),
                      (cx_c+38, cy_c + 8),
                      (cx_c+14, cy_c + 8)]
            pygame.draw.polygon(self.screen, col_v, poly_v)

            self.draw_text(cd["name"], (cx_c, by + card_h - 24), 15,
                           (255,230,50) if sel else (180,180,220))
            self.draw_text("P" , (cx_c - 8, by + card_h - 8), 11, col_p)
            self.draw_text("V" , (cx_c + 8, by + card_h - 8), 11, col_v)
            if sel:
                pygame.draw.rect(self.screen, (255,230,50), card, 3, border_radius=10)

        # 선택된 색상 미리보기 (크게)
        sel_cd = SHIP_COLORS[self.color_select_idx]
        preview_x, preview_y = 400, 555
        big_scale = 28
        big_poly = [(preview_x, preview_y - big_scale),
                    (preview_x + big_scale, preview_y + big_scale),
                    (preview_x - big_scale, preview_y + big_scale)]
        pygame.draw.polygon(self.screen, sel_cd["color_p"], big_poly)
        pygame.draw.polygon(self.screen, (255,255,255), big_poly, 1)
        self.draw_text(f"선택: {sel_cd['name']}", (400, preview_y + big_scale + 14), 17, (255,230,80))

    # ─────────────────────────────────────
    def _draw_rift(self, shake):
        """제3차원 전투 화면"""
        # ── 독특한 배경: 진보라+자줏빛 ──
        pulse = int(20 + 15 * math.sin(self.rift_timer * 0.04))
        self.screen.fill((10, 0, pulse + 8))

        # 제3차원 격자 배경
        cam = self.camera_offset + shake
        grid_col = (40, 0, 80)
        grid_spacing = 80
        offset_x = int(-cam.x % grid_spacing)
        offset_y = int(-cam.y % grid_spacing)
        for gx in range(-1, self.SW // grid_spacing + 2):
            lx = offset_x + gx * grid_spacing
            pygame.draw.line(self.screen, grid_col, (lx, 0), (lx, self.SH), 1)
        for gy in range(-1, self.SH // grid_spacing + 2):
            ly = offset_y + gy * grid_spacing
            pygame.draw.line(self.screen, grid_col, (0, ly), (self.SW, ly), 1)

        # 중심 포탈 링 (탈출구 — 보스 처치 후 빛남)
        pcx = int(0 - cam.x); pcy = int(-200 - cam.y)
        for ri, (r, alpha, col) in enumerate([
            (80, 40, (100, 0, 200)),
            (55, 80, (160, 0, 255)),
            (30, 150, (220, 100, 255)),
        ]):
            try:
                s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(s, (*col, alpha), (r+2, r+2), r, 4)
                self.screen.blit(s, (pcx-r-2, pcy-r-2))
            except Exception:
                pass

        # 별 (보라톤)
        rng2 = random.Random(77)
        for _ in range(80):
            sx = rng2.randint(0,800); sy = rng2.randint(0,600)
            b  = rng2.randint(40,130)
            pygame.draw.circle(self.screen, (b//2, 0, b), (sx, sy), 1)

        # 적 렌더링
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

        # 탄환
        for p in self.rift_projectiles:
            p.update_screen_pos(cam)
            self.screen.blit(p.image, p.rect)
        for ep in self.rift_ep:
            ep.update_screen_pos(cam)
            self.screen.blit(ep.image, ep.rect)

        # 플레이어
        self.screen.blit(self.player.image, self.player.rect)

        # 파티클
        for particle in self.rift_particles:
            particle.draw(self.screen, cam)

        # 조준 커서
        mx, my = self.mouse_pos
        pygame.draw.circle(self.screen, (200,80,255), (mx,my), 7, 1)
        pygame.draw.line(self.screen, (200,80,255), (mx-12,my),(mx+12,my), 1)
        pygame.draw.line(self.screen, (200,80,255), (mx,my-12),(mx,my+12), 1)

        # HUD (제3차원용)
        self._draw_rift_hud()

        # 화이트/보라 플래시 오버레이
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
        # HP 바
        hp_ratio = max(0, self.player.health/self.player.max_health)
        hw = 170
        pygame.draw.rect(self.screen,(50,8,8),(10,26,hw,15),border_radius=4)
        hpc = (80,255,80) if hp_ratio>0.6 else ((255,200,0) if hp_ratio>0.3 else (255,50,50))
        pygame.draw.rect(self.screen,hpc,(10,26,int(hw*hp_ratio),15),border_radius=4)
        pygame.draw.rect(self.screen,(100,100,130),(10,26,hw,15),1,border_radius=4)
        self.draw_text(f"HP {self.player.health}/{self.player.max_health}",(10+hw//2,33),14)

        # 보스 HP 바 (상단 중앙 크게)
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

        # 제3차원 표시 + 처치 횟수
        self.draw_text("⚡ 제3차원 ⚡", (660,18), 17, (200,80,255))
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
        self.screen.fill(bg)
        self.star_field.draw(self.screen, self.camera_offset,
                              self.dimension, abyss=self.abyss_active)

        # 심해 차원 오버레이 (반투명 파란 파동)
        if self.abyss_active:
            pulse = int(30 + 20 * math.sin(self.game_time * 0.05))
            try:
                ov = pygame.Surface((800,600), pygame.SRCALPHA)
                ov.fill((0, pulse, pulse*2, 18))
                self.screen.blit(ov, (0,0))
            except Exception:
                pass

        # ── 블랙홀 흡입 트랜지션 이펙트 ──
        if self.bh_suck_timer > 0:
            t = self.bh_suck_timer / 60.0  # 1→0
            # 화면 가장자리 점점 어두워지는 비네트
            try:
                vignette = pygame.Surface((800,600), pygame.SRCALPHA)
                vignette.fill((0,0,0,0))
                edge_alpha = int((1-t) * 220)
                pygame.draw.rect(vignette, (0,0,0,edge_alpha), (0,0,800,600))
                # 중앙 구멍 (원형 마스크)
                hole_r = int(t * 320)
                pygame.draw.circle(vignette, (0,0,0,0), (400,300), hole_r)
                self.screen.blit(vignette, (0,0))
            except Exception:
                pass
            # 소용돌이 링들
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
            # 텍스트
            alpha_t = int((1-t) * 255)
            msg_surf = self._get_font(26).render("블랙홀에 흡입됨...", True, (200, 80, 255))
            msg_surf.set_alpha(alpha_t)
            self.screen.blit(msg_surf, msg_surf.get_rect(center=(400, 300)))

        # 화이트/보라 플래시 (제3차원 진입/탈출 시)
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
            # ship_form 아이템 빛남
            self.screen.blit(item.image, item.rect)

        for gem in self.gems:
            gem.update_screen_pos(cam)
            self.screen.blit(gem.image, gem.rect)

        # 블랙홀
        for bh in self.blackholes:
            bh.draw(self.screen, cam, self.game_time)

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

        for p in self.projectiles:
            p.update_screen_pos(cam)
            self.screen.blit(p.image, p.rect)

        for ep in self.enemy_projectiles:
            ep.update_screen_pos(cam)
            if ep.dimension == self.dimension or self.abyss_active:
                self.screen.blit(ep.image, ep.rect)

        for comp in self.companions:
            self.screen.blit(comp.image, comp.rect)

        self.screen.blit(self.player.image, self.player.rect)

        for particle in self.particles:
            particle.draw(self.screen, cam)

        # 조준 커서
        mx,my = self.mouse_pos
        col_c = (0,220,255) if self.abyss_active else (255,255,100)
        pygame.draw.circle(self.screen, col_c, (mx,my), 7, 1)
        pygame.draw.line(self.screen, col_c, (mx-12,my),(mx+12,my), 1)
        pygame.draw.line(self.screen, col_c, (mx,my-12),(mx,my+12), 1)

        self._draw_hud(progress)
        self._draw_minimap()

        if self.abyss_active:
            self._draw_abyss_bar()

        if self.form_select_active:
            self._draw_form_select()
        elif self.levelup_active:
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

    def _draw_abyss_bar(self):
        """심해 차원 남은 시간 바 — 화면 상단"""
        remain = self.abyss_timer / self.ABYSS_DURATION
        pulse  = int(200 + 55*math.sin(self.game_time*0.1))
        pygame.draw.rect(self.screen, (0,30,60), (10,595,780,4))
        pygame.draw.rect(self.screen, (0,pulse,255), (10,595,int(780*remain),4))
        sec = self.abyss_timer // 60
        self.draw_text(f"심해 차원 {sec}s", (400,590), 15, (0,200,255))

    def _draw_hud(self, progress):
        # XP 바
        fill_w = int((self.player.xp/self.player.xp_to_next)*780)
        pygame.draw.rect(self.screen,(22,22,38),(10,10,780,11))
        pygame.draw.rect(self.screen,(0,220,100),(10,10,fill_w,11))
        pygame.draw.rect(self.screen,(45,45,65),(10,10,780,11),1)

        # HP 바
        hp_ratio = max(0, self.player.health/self.player.max_health)
        hw = 170
        pygame.draw.rect(self.screen,(50,8,8),(10,26,hw,15),border_radius=4)
        hpc = (80,255,80) if hp_ratio>0.6 else ((255,200,0) if hp_ratio>0.3 else (255,50,50))
        if self.player.invincible>0 and (self.player.invincible//5)%2==0: hpc=(255,255,255)
        pygame.draw.rect(self.screen,hpc,(10,26,int(hw*hp_ratio),15),border_radius=4)
        pygame.draw.rect(self.screen,(100,100,130),(10,26,hw,15),1,border_radius=4)
        self.draw_text(f"HP {self.player.health}/{self.player.max_health}",(10+hw//2,33),14)

        # 쉴드
        if self.player.max_shield > 0:
            sr = self.player.shield/self.player.max_shield; sw=80
            pygame.draw.rect(self.screen,(0,20,50),(185,26,sw,15),border_radius=4)
            pygame.draw.rect(self.screen,(0,150,255),(185,26,int(sw*sr),15),border_radius=4)
            pygame.draw.rect(self.screen,(0,100,200),(185,26,sw,15),1,border_radius=4)
            self.draw_text(f"SH{self.player.shield}",(185+sw//2,33),14,(100,200,255))

        # 타이머 — 시간 초과 후 보스 처치 대기 중이면 경고 표시
        tl = max(0, self.current_chapter.duration - self.game_time//60)
        if tl == 0:
            final_bosses = ["void_god","abyss_sovereign","nexus_overmind","abyssal_tyrant"]
            alive_finals = [e for e in self.enemies if e.etype in final_bosses]
            if alive_finals:
                # 깜빡이는 경고
                col = (255,80,80) if (self.game_time // 20) % 2 == 0 else (255,200,80)
                self.draw_text("★ 최종 보스 처치! ★",(400,32),22,col)
            else:
                self.draw_text("00:00",(400,32),28)
        else:
            self.draw_text(f"{tl//60:02d}:{tl%60:02d}",(400,32),28)

        # 점수
        self.draw_text(f"{self.player.score:,}",(600,32),22,(255,220,80))

        # 균열 보스 처치 수 표시
        if self.rift_boss_kill_count > 0:
            self.draw_text(f"⚫×{self.rift_boss_kill_count}",(720,32),16,(200,100,255))

        # 레벨/차원/무기/대쉬/변형
        form = SHIP_FORMS.get(self.player.ship_form, SHIP_FORMS["fighter"])
        dash_ready = "●" if self.player.dash_cd==0 else f"○{self.player.dash_cd//10}"
        dim_txt  = "ABYSS" if self.abyss_active else self.dimension[0]
        self.draw_text(
            f"LV:{self.player.level}  [{dim_txt}]  {self.player.weapon['name']}  {dash_ready}",
            (210,52),16,(255,230,80))
        self.draw_text(f"[{form['name']}]",(620,52),14,(180,220,255))

        # 설정 버튼 힌트 (우측 상단)
        cfg_col = (0, 220, 255) if self.settings_open else (70, 90, 110)
        self.draw_text("⚙ ESC/TAB", (760, 52), 12, cfg_col)

        # 진행도 바
        pygame.draw.rect(self.screen,(14,14,28),(10,583,780,7))
        pygame.draw.rect(self.screen,(0,140,255),(10,583,int(780*progress),7))

        # 무기 목록
        for i,wk in enumerate(self.player.unlocked_weapons):
            wi = WEAPONS[wk]; active = (wk==self.player.weapon_key)
            col = (255,230,80) if active else (70,70,95)
            pygame.draw.rect(self.screen,(16,16,28),(10+i*78,554,74,22),border_radius=3)
            if active: pygame.draw.rect(self.screen,col,(10+i*78,554,74,22),1,border_radius=3)
            self.draw_text(wi["name"],(47+i*78,564),13,col)

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

        # 블랙홀
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

            # 변형 미리보기 (폴리곤)
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
        self.screen.fill((28,4,4))
        rng=random.Random(self.game_time)
        for _ in range(60):
            x=rng.randint(0,800); y=rng.randint(0,600)
            pygame.draw.circle(self.screen,(rng.randint(80,180),0,0),(x,y),1)
        self.draw_text("MISSION FAILED",(400,235),60,(255,40,40))
        if self.player:
            self.draw_text(f"점수: {self.player.score:,}",(400,316),32,(255,200,80))
            self.draw_text(f"처치: {self.player.kill_count}  최대 콤보: {self.player.max_combo}  LV: {self.player.level}",(400,362),20,(170,170,200))
            form = SHIP_FORMS.get(self.player.ship_form, SHIP_FORMS["fighter"])
            self.draw_text(f"최종 변형: {form['name'].split('(')[0]}",(400,392),18,(180,220,255))
        self.draw_text(f"최고 점수: {self.high_score:,}",(400,428),22,(255,230,100))
        self.draw_text("Press [R] — 메뉴로",(400,480),24,(140,140,170))

    def _draw_win(self):
        self.screen.fill((4,22,8))
        rng=random.Random(self.game_time)
        for _ in range(80):
            x=rng.randint(0,800); y=rng.randint(0,600)
            pygame.draw.circle(self.screen,(0,rng.randint(80,180),rng.randint(40,100)),(x,y),1)
        self.draw_text("CHAPTER CLEARED!",(400,210),54,(0,255,100))
        if self.player:
            self.draw_text(f"점수: {self.player.score:,}",(400,285),32,(255,220,80))
            self.draw_text(f"처치: {self.player.kill_count}  최대 콤보: {self.player.max_combo}  LV: {self.player.level}",(400,330),20,(170,200,170))
        if self.rift_boss_kill_count > 0:
            self.draw_text(f"⚫ 균열 보스 처치: {self.rift_boss_kill_count}회",(400,362),20,(200,100,255))
        self.draw_text(f"최고 점수: {self.high_score:,}",(400,398),22,(255,230,100))
        self.draw_text("Press [M] — 메뉴로",(400,456),24,(90,200,130))

    # ─────────────────────────────────────
    def _get_font(self, size):
        if not hasattr(self,"_font_cache"): self._font_cache={}
        if size not in self._font_cache:
            import os
            candidates=["C:/Windows/Fonts/malgun.ttf","C:/Windows/Fonts/gulim.ttc",
                        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
                        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]
            font=None
            for path in candidates:
                if os.path.exists(path):
                    try: font=pygame.font.Font(path,size); break
                    except Exception: continue
            if font is None:
                for name in ["malgun gothic","맑은 고딕","gulim"]:
                    try:
                        f=pygame.font.SysFont(name,size)
                        if f: font=f; break
                    except Exception: continue
            if font is None: font=pygame.font.SysFont(None,size)
            self._font_cache[size]=font
        return self._font_cache[size]

    def draw_text(self, text, pos, size, color=(255,255,255)):
        font=self._get_font(size)
        img =font.render(text,True,color)
        rect=img.get_rect(center=pos)
        self.screen.blit(img,rect)