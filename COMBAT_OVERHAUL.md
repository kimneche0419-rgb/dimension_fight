# ⚔️ DIMENSION FIGHT — 전투 시스템 완전 개혁안
> **기존 시스템과 완전히 다른 방향의 전투·스킬·적 공격 패턴 설계서**

---

## 🔴 1. 적 공격 시스템 — 변칙 패턴 리디자인

### 현재 문제점
- 모든 적의 공격이 `ranged_shot / burst_shot / phase_boss` 세 종류로 수렴
- 탄환은 직선 이동 후 일정 시간 뒤 `kill()` — 완전히 예측 가능
- 거리 기반 행동(if dist > 400: 돌격) 단순 반복

---

### 🆕 NEW: 적 공격 유형 8가지 (완전 교체)

---

#### [TYPE-1] 🌀 ECHO SHOT — 기억 탄환
> "플레이어가 1초 전에 있던 위치를 향해 발사"

```python
# enemy.py 내 추가
class EchoShot:
    """
    플레이어의 과거 위치 기록을 추적해 발사.
    피하면 피할수록 예측이 어긋남 — 하지만 멈추면 맞음.
    """
    HISTORY_LEN = 60  # 60프레임(1초) 전 위치

    def __init__(self):
        self.pos_history = []  # [(x, y), ...]

    def record(self, player_pos):
        self.pos_history.append(Vector2(player_pos))
        if len(self.pos_history) > self.HISTORY_LEN:
            self.pos_history.pop(0)

    def get_target(self):
        if len(self.pos_history) >= self.HISTORY_LEN:
            return self.pos_history[0]  # 1초 전 위치
        return None

# 발사 조건: special_timer % 75 == 0 and len(pos_history) == HISTORY_LEN
# 탄속: 9  / 데미지: 10
# 적용 적: sniper_node, leviathan_eye, echo_wraith
```

**전투 변화:**
- 대쉬로 피하면 피할수록 탄환이 "과거의 내 위치"를 추적
- 멈추면 반드시 맞는 심리전 탄환
- `void_wraith_king`의 전용 패턴으로 배치 가능

---

#### [TYPE-2] 💥 MINE FIELD — 지연 폭발 지뢰
> "발사 즉시 화면에 정지하고 3초 후 반경 180px 폭발"

```python
class DelayedMine(pygame.sprite.Sprite):
    def __init__(self, world_pos, dimension, dmg=18):
        self.world_pos = Vector2(world_pos)
        self.fuse = 180       # 3초 (60fps 기준)
        self.dmg  = dmg
        self.exploded = False
        self.radius   = 180   # 폭발 반경
        # 이미지: 점멸하는 붉은 마름모
        # fuse < 60: 점멸 속도 2배 (경고)
        # fuse < 20: 빨간 플래시

    def update(self, player_pos, screen_shake_fn, burst_fn):
        self.fuse -= 1
        if self.fuse <= 0:
            self.exploded = True
            dist = (player_pos - self.world_pos).length()
            if dist < self.radius:
                dmg_scaled = int(self.dmg * (1 - dist / self.radius))
                # player.take_hit(dmg_scaled)
            screen_shake_fn(20, 18)
            burst_fn(self.world_pos, (255, 80, 0), count=50, speed=12)
            self.kill()

# 적용 적: dreadnought_construct (필드 3개 동시 배치)
# 특이점: 플레이어가 지뢰 주위를 원으로 돌아서 무력화 가능 (지뢰 중첩 회피)
```

---

#### [TYPE-3] 🪞 MIRROR BOLT — 벽 반사 탄환
> "맵 경계(가상 벽 ±2000px)에서 반사되어 다시 돌아옴"

```python
class MirrorBolt(pygame.sprite.Sprite):
    BOUNDARY = 2000   # 월드 경계

    def update(self):
        self.world_pos += self.vel
        # X 반사
        if abs(self.world_pos.x) > self.BOUNDARY:
            self.vel.x *= -1
            self.bounces_x += 1
        # Y 반사
        if abs(self.world_pos.y) > self.BOUNDARY:
            self.vel.y *= -1
            self.bounces_y += 1
        # 총 3회 반사 후 소멸
        if self.bounces_x + self.bounces_y >= 3:
            self.kill()

# 속도: 7   / 데미지: 12   / 반사 횟수: 3
# 발사 각도: 플레이어 방향 ± 30도 (랜덤)
# 적용 적: void_weaver, null_colossus
# 색상: 반사마다 색 변화 (흰→노랑→주황)
```

---

#### [TYPE-4] 🧲 GRAVITY PULL SHOT — 중력 탄환
> "탄환 자체가 중력장을 가짐 — 플레이어 속도에 영향"

```python
class GravityBolt(pygame.sprite.Sprite):
    """
    탄환에 접근하면 플레이어가 느려지고(끌림),
    탄환을 지나치면 반발력으로 가속됨.
    직접 맞추기가 오히려 어려운 특수 탄.
    """
    PULL_RANGE  = 140   # 이 범위 안에 들어오면 속도 감소
    PULL_FORCE  = 0.4   # 플레이어 속도 감속 계수

    def apply_gravity(self, player_vel, player_pos):
        d_vec = self.world_pos - player_pos
        dist  = d_vec.length()
        if dist < self.PULL_RANGE and dist > 0:
            # 가까울수록 더 강하게 끌림
            force = self.PULL_FORCE * (1 - dist / self.PULL_RANGE)
            player_vel += d_vec.normalize() * force
        return player_vel

# 탄속: 5  / 데미지: 8 (범위형, 반경 40px)
# 적용 적: gravity_core, gravity_orb
```

---

#### [TYPE-5] 🌊 WAVE PULSE — 확산파 공격
> "적 자신을 중심으로 링형 충격파를 외향 방사"

```python
class WavePulse:
    """
    탄환이 아닌 '반경'이 무기.
    발사 직후 반경 0에서 시작해 350px까지 확대.
    플레이어가 확산 링과 겹치면 피격.
    안쪽으로 다가가거나 아주 멀리 있으면 안전.
    """
    def __init__(self, world_pos, max_radius=350, expand_speed=6, dmg=14):
        self.world_pos   = Vector2(world_pos)
        self.radius      = 0
        self.max_radius  = max_radius
        self.expand_speed= expand_speed
        self.dmg         = dmg
        self.hit_band    = 22   # 링의 두께
        self.done        = False

    def update(self, player_pos):
        self.radius += self.expand_speed
        if self.radius >= self.max_radius:
            self.done = True
        dist = (player_pos - self.world_pos).length()
        # 링 범위 내에 있으면 피격
        if abs(dist - self.radius) < self.hit_band:
            return True   # 피격 신호
        return False

    def draw(self, surface, cam):
        cx = int(self.world_pos.x - cam.x)
        cy = int(self.world_pos.y - cam.y)
        alpha = int(200 * (1 - self.radius / self.max_radius))
        # SRCALPHA 서피스로 링 드로잉
        r = int(self.radius)
        s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 100, 0, alpha), (r+2, r+2), r, 6)
        surface.blit(s, (cx - r - 2, cy - r - 2))

# 발동 조건: special_timer % 200 == 0
# 적용 적: anomaly_core, entropy_core (단계별 속도 증가)
```

---

#### [TYPE-6] 👁️ CURSOR LOCK — 마우스 추적 탄환
> "플레이어의 마우스 커서 위치를 직접 추적"

```python
class CursorLockShot:
    """
    기존 탄환: 발사 시점의 플레이어 위치 → 직선
    이 탄환:   발사 후에도 마우스 커서 방향으로 회전
    
    조준을 계속 바꾸면 탄환이 따라옴.
    조준을 고정하면 탄환이 직선으로 빠르게 날아옴.
    """
    TURN_SPEED = 2.5   # 도/프레임

    def update(self, mouse_world_pos):
        # 탄환 → 마우스 사이 각도 계산
        to_mouse = mouse_world_pos - self.world_pos
        if to_mouse.length() > 0:
            target_angle = math.degrees(math.atan2(to_mouse.y, to_mouse.x))
            current_angle = math.degrees(math.atan2(self.vel.y, self.vel.x))
            da = (target_angle - current_angle + 180) % 360 - 180
            da = max(-self.TURN_SPEED, min(self.TURN_SPEED, da))
            new_angle = current_angle + da
            spd = self.vel.length()
            self.vel = Vector2(math.cos(math.radians(new_angle)),
                               math.sin(math.radians(new_angle))) * spd
        self.world_pos += self.vel

# 탄속: 6 (시작) → 최대 11 (3초 후 가속)
# 데미지: 16  /  지속: 240프레임
# 적용 적: rift_guardian, void_god (4페이즈 전용)
# 대응책: 마우스를 탄환 반대편으로 이동 → 유인 후 대쉬
```

---

#### [TYPE-7] 🔗 CHAIN LIGHTNING — 연쇄 번개
> "플레이어 맞으면 → 탄환으로 반사 → 탄환이 다시 플레이어에게 튕김"

```python
class ChainLightning:
    """
    번개가 플레이어에게 맞으면 1회,
    화면 내 아군 탄환(Projectile)에게 반사 후 다시 플레이어에게.
    총 최대 3회 연쇄.
    
    탄환이 많을수록 오히려 위험해지는 역설.
    탄환을 아끼거나 공간을 비우는 새로운 전술 강요.
    """
    MAX_BOUNCES = 3
    BOUNCE_RANGE = 250

    def bounce(self, player_pos, projectile_group):
        if self.bounces >= self.MAX_BOUNCES:
            self.kill(); return

        # 가장 가까운 아군 탄환 찾기
        nearest_proj = None
        min_d = self.BOUNCE_RANGE
        for p in projectile_group:
            d = (p.world_pos - self.world_pos).length()
            if d < min_d:
                min_d = d; nearest_proj = p

        if nearest_proj:
            # 탄환으로 반사
            self.target = nearest_proj.world_pos
            self.bounces += 1
            self.dmg = int(self.dmg * 0.7)  # 반사마다 약해짐
        else:
            # 반사 대상 없으면 즉시 소멸
            self.kill()

# 적용 적: echo_wraith, rift_colossus
# 시각 효과: 반사 시 지그재그 번개선 드로잉 (pygame.draw.lines)
```

---

#### [TYPE-8] 🕳️ VOID ANCHOR — 이동 봉인 탄환
> "맞으면 3초간 플레이어를 특정 지점에 '닻'으로 고정"

```python
class VoidAnchor:
    """
    맞는 순간 플레이어의 이동 반경을 반경 80px로 제한.
    닻 중심으로부터 80px 이상 멀어지려 하면 
    고무줄처럼 당겨옴.
    대쉬로 순간적으로 벗어날 수 있음.
    """
    ANCHOR_RANGE = 80
    PULL_BACK    = 0.35   # 당김 강도
    DURATION     = 180    # 3초

    # player 측 적용 로직
    def apply_anchor(self, player):
        if not self.active: return
        self.timer -= 1
        if self.timer <= 0:
            self.active = False; return
        dist = (player.world_pos - self.anchor_pos).length()
        if dist > self.ANCHOR_RANGE:
            pull = (self.anchor_pos - player.world_pos).normalize()
            player.vel += pull * self.PULL_BACK * (dist / self.ANCHOR_RANGE)
        # 대쉬로 해제 가능
        if player.dash_timer > 0:
            self.active = False

# 적용 적: abyss_rift_lord (2페이즈 이후)
# 시각 효과: 닻 위치에서 플레이어까지 보라색 체인 선
```

---

## 🟡 2. 전투 방식 — 변칙 메카닉 5종

### [MECH-1] 🔄 DIMENSIONAL ECHO — 차원 잔상 전투

**개념:** 차원 전환(SHIFT) 시 0.5초간 "잔상(Ghost)"이 이전 차원에 남아 적의 공격을 1회 대신 받음

```python
class DimensionalGhost:
    """
    SHIFT로 차원 전환 직후 30프레임(0.5초) 동안
    이전 차원에 반투명 잔상이 생성됨.
    
    적 탄환이 잔상에 맞으면:
    - PHYSICAL 잔상 → 공격력 20% 로 반사탄 생성
    - VOID 잔상     → 해당 탄환 흡수 후 HP +3 회복
    
    전략: 일부러 탄환을 맞을 타이밍에 차원 전환
    """
    def __init__(self, pos, dimension, color):
        self.world_pos = Vector2(pos)
        self.dimension = dimension
        self.life = 30
        self.color = (*color, 90)  # 반투명

    def update(self, enemy_projectiles, player):
        self.life -= 1
        for ep in list(enemy_projectiles):
            if ep.dimension == self.dimension:
                dist = (self.world_pos - ep.world_pos).length()
                if dist < 20:
                    if self.dimension == "PHYSICAL":
                        # 반사탄 생성
                        return "REFLECT", ep
                    else:
                        # 흡수 후 HP 회복
                        player.health = min(player.max_health, player.health + 3)
                        ep.kill()
        return None, None
```

---

### [MECH-2] 🎯 WEAK POINT SYSTEM — 부위 파괴

**개념:** 보스급 적에게 "코어(Core)" 부위 표시 — 거기에만 크리티컬 배율 적용

```python
# Enemy 클래스 내 추가
class WeakPoint:
    """
    max_hp >= 100 인 적(보스)에게 활성화.
    
    코어 위치: 적 이미지 중앙 ± 랜덤 오프셋 (페이즈마다 이동)
    코어 크기: 반경 12px
    
    코어 피격: 데미지 × 3.0 (크리티컬)
    코어 이외: 데미지 × 0.6 (방어막 적용)
    
    코어는 3초마다 위치 변경 (페이즈 2 이후: 1.5초마다)
    """
    def __init__(self, enemy_size):
        sz = enemy_size // 2
        self.offset = Vector2(
            random.randint(-sz//2, sz//2),
            random.randint(-sz//2, sz//2)
        )
        self.timer = 180  # 3초

    def update(self, enemy_size, phase):
        self.timer -= 1
        interval = 90 if phase >= 2 else 180
        if self.timer <= 0:
            self.timer = interval
            sz = enemy_size // 2
            self.offset = Vector2(
                random.randint(-sz//2, sz//2),
                random.randint(-sz//2, sz//2)
            )

    def check_hit(self, hit_pos, enemy_center):
        dist = (hit_pos - (enemy_center + self.offset)).length()
        return dist < 12  # 크리티컬 여부

# engine.py 충돌 처리 수정:
# if weak_point.check_hit(p.world_pos, enemy.world_pos):
#     dmg *= 3.0  # 크리티컬
#     burst(enemy.world_pos, (255,255,0), count=20)
# else:
#     dmg *= 0.6
```

---

### [MECH-3] 💡 ADAPTIVE ARMOR — 적응형 방어구

**개념:** 같은 무기를 반복 사용하면 적이 해당 무기에 면역이 생김

```python
# Enemy 클래스 내 추가
class AdaptiveArmor:
    """
    적이 동일 무기(weapon_key)에 맞을 때마다
    내성 카운터 증가.
    
    맞은 횟수별 배율:
      0~2회: ×1.0 (기본)
      3~5회: ×0.7 (내성 형성 중)
      6~9회: ×0.4 (강한 내성)
     10회+:  ×0.1 (거의 무효)
    
    다른 무기로 교체하면 내성 리셋.
    → 무기 로테이션을 강제하는 전술 메카닉
    """
    def __init__(self):
        self.hit_log = {}  # {weapon_key: count}
        self.last_weapon = None

    def get_resist_mult(self, weapon_key):
        if weapon_key != self.last_weapon:
            self.hit_log[weapon_key] = 0
            self.last_weapon = weapon_key
        count = self.hit_log.get(weapon_key, 0)
        self.hit_log[weapon_key] = count + 1
        if count < 3:  return 1.0
        if count < 6:  return 0.7
        if count < 10: return 0.4
        return 0.1

# 적용 대상: elite_enforcer, void_god, abyss_sovereign (보스급)
# UI: 적 HP바 위에 현재 내성 아이콘 표시 (방패 심볼 + 색상)
```

---

### [MECH-4] ⚡ ENERGY DRAIN — 에너지 흡수 전투

**개념:** 스킬을 사용할수록 충전되는 "BURST 게이지" — 100% 시 스킬이 2배 강해짐

```python
class BurstGauge:
    """
    기존: 스킬 쿨타임만 존재
    변경: 스킬 사용 + 적 처치로 게이지 충전
    
    게이지 100% = BURST MODE 10초
    BURST MODE 중:
    - 모든 스킬 데미지 × 2.0
    - 스킬 쿨타임 50% 감소
    - 탄환에 에너지 잔상 효과
    
    충전량:
    - 스킬 1회 사용:     +8%
    - 일반 적 처치:      +2%
    - 보스 부위 파괴:    +15%
    - 차원 전환 반사:    +5%
    """
    def __init__(self):
        self.gauge = 0.0       # 0.0 ~ 1.0
        self.burst_timer = 0   # 활성 시간 (프레임)
        self.BURST_DURATION = 600  # 10초

    @property
    def is_burst(self):
        return self.burst_timer > 0

    def charge(self, amount):
        if self.is_burst: return
        self.gauge = min(1.0, self.gauge + amount)
        if self.gauge >= 1.0:
            self.gauge = 0.0
            self.burst_timer = self.BURST_DURATION

    def update(self):
        if self.burst_timer > 0:
            self.burst_timer -= 1

    def get_skill_mult(self):
        return 2.0 if self.is_burst else 1.0

    def get_cd_mult(self):
        return 0.5 if self.is_burst else 1.0
```

---

### [MECH-5] 🌪️ ENVIRONMENT HAZARD — 전장 환경 무기화

**개념:** 맵 내 구조물·유체가 전투에 직접 개입하는 "환경 무기" 시스템

```python
class EnvironmentCombat:
    """
    구조물(Structure)에 탄환을 충돌시키면
    충돌점에서 파편 스플래시 발생.
    
    파편 데미지: 원래 탄환 데미지 × 0.5
    파편 개수:   6개 (랜덤 방향)
    파편 범위:   100px
    
    유체(Fluid) 위에서 전투 시:
    - 물리 탄환(PHYSICAL)이 유체에 닿으면 전기 장판으로 변환
    - 전기 장판: 반경 150px, 3초 지속, 지속 데미지 (5/s)
    
    적이 유체 위에 있으면:
    - 이동속도 ×0.6 (플레이어도 동일)
    - 전기 장판에 피격 시 일시 마비 (0.5초 정지)
    """
    @staticmethod
    def on_projectile_hit_structure(proj_pos, proj_dmg, structures):
        fragments = []
        for s in structures:
            if s.get_world_rect().collidepoint(proj_pos.x, proj_pos.y):
                for _ in range(6):
                    angle = random.uniform(0, 360)
                    spd   = random.uniform(3, 7)
                    vel   = Vector2(math.cos(math.radians(angle)) * spd,
                                    math.sin(math.radians(angle)) * spd)
                    fragments.append({
                        "pos":  Vector2(proj_pos),
                        "vel":  vel,
                        "dmg":  proj_dmg * 0.5,
                        "life": 20
                    })
                break
        return fragments

    @staticmethod
    def on_projectile_hit_fluid(proj_pos, proj_dimension, fluids, hazards_list):
        if proj_dimension != "PHYSICAL": return
        for f in fluids:
            if f.get_world_rect().collidepoint(proj_pos.x, proj_pos.y):
                hazards_list.append({
                    "pos":    Vector2(proj_pos),
                    "radius": 150,
                    "timer":  180,   # 3초
                    "dmg_per_sec": 5,
                    "type":   "electric"
                })
                break
```

---

## 🟢 3. 스킬 시스템 — 완전 재설계

### 현재 문제점
- 스킬은 "쿨타임만 있는 버튼" — 전략적 선택 없음
- 레벨업은 단순 수치 상승
- 스킬 간 시너지 없음

---

### 🆕 NEW: RESONANCE SYSTEM — 공명 스킬 체계

**핵심 개념:** 스킬을 단독으로 쓰면 기본 효과, **2개 이상 조합**하면 완전히 다른 효과 발동

---

#### 공명 조합표

| 1번 스킬 | 2번 스킬 | 공명 효과 | 이름 |
|---|---|---|---|
| 노바 블래스트 | 타임 워프 | 느려진 공간에서 연속 노바 3회 | **TEMPORAL NOVA** |
| 월아천충 | 아마테라스 | 흑염이 붙은 거대 섬광 발사 | **BLACK STAR** |
| 무량공처 | 중력 서지 | 얼어붙은 적을 블랙홀로 압축 | **SINGULARITY FREEZE** |
| 뱀파이어리즘 | 그림자 추출 | 그림자 군대가 HP를 흡혈 | **SHADOW TIDE** |
| 진격의 거인 | 뇌창 | 거인 형태로 뇌창을 5발 동시 투척 | **TITAN BARRAGE** |
| 쉴드 오버로드 | 스텔스 클로킹 | 무적+투명+공격력×3 (1.5초) | **GHOST PROTOCOL** |

```python
class ResonanceSystem:
    """
    스킬 A 사용 후 3초(180프레임) 이내에
    스킬 B를 사용하면 공명 발동.
    
    공명 발동 시:
    - 두 스킬의 쿨타임 각각 50% 차감 (보너스)
    - 특수 이펙트 + 데미지 × 2.5
    - BURST 게이지 +30% 충전
    """
    COMBOS = {
        ("nova_blast",     "time_warp"):       "temporal_nova",
        ("getsuga_tensho", "amaterasu"):       "black_star",
        ("infinite_void",  "gravity_surge"):   "singularity_freeze",
        ("vampirism",      "shadow_extraction"):"shadow_tide",
        ("titan_form",     "thunder_spear"):   "titan_barrage",
        ("shield_overload","stealth_cloak"):   "ghost_protocol",
    }

    def __init__(self):
        self.last_skill    = None
        self.last_skill_time = 0   # 프레임 카운터
        self.frame         = 0

    def tick(self):
        self.frame += 1

    def try_resonate(self, new_skill):
        if self.last_skill and self.frame - self.last_skill_time <= 180:
            pair = (self.last_skill, new_skill)
            pair_rev = (new_skill, self.last_skill)
            if pair in self.COMBOS:
                result = self.COMBOS[pair]
                self.last_skill = None
                return result
            if pair_rev in self.COMBOS:
                result = self.COMBOS[pair_rev]
                self.last_skill = None
                return result
        self.last_skill      = new_skill
        self.last_skill_time = self.frame
        return None   # 공명 없음, 기본 스킬 발동
```

---

### 🆕 NEW: SKILL MUTATION — 스킬 돌연변이

**개념:** 스킬을 일정 횟수 사용하면 형태가 **변이**하여 완전히 다른 스킬로 진화

```
노바 블래스트 (10회 사용) → DARK NOVA
  기존: 주변 광역 데미지
  변이: 블랙홀 3개 동시 생성 (5초) + 흡수된 적은 아군으로 부활

타임 워프 (8회 사용) → TIME COLLAPSE
  기존: 적 속도 감소
  변이: 3초간 모든 탄환/적 완전 정지 + 플레이어만 2배속

뇌창 (15회 사용) → MJOLNIR
  기존: 폭발 투척
  변이: 화면 전체에 낙뢰 12발 동시 낙하 (랜덤 위치)

월아천충 (12회 사용) → FINAL GETSUGA
  기존: 단일 고데미지 투사체
  변이: 플레이어 주위 360도 동시 방사 (전방향 공격)
```

```python
SKILL_MUTATION_DATA = {
    "nova_blast": {
        "threshold": 10,
        "mutated_name": "DARK NOVA",
        "mutated_key":  "dark_nova",
        "desc": "블랙홀 3개 생성 + 적 부활"
    },
    "time_warp": {
        "threshold": 8,
        "mutated_name": "TIME COLLAPSE",
        "mutated_key":  "time_collapse",
        "desc": "3초간 완전 동결 + 플레이어 2배속"
    },
    "thunder_spear": {
        "threshold": 15,
        "mutated_name": "MJOLNIR",
        "mutated_key":  "mjolnir",
        "desc": "전화면 낙뢰 12발 동시 낙하"
    },
    "getsuga_tensho": {
        "threshold": 12,
        "mutated_name": "FINAL GETSUGA",
        "mutated_key":  "final_getsuga",
        "desc": "360도 전방향 동시 방사"
    },
}

# Player 클래스 내 추가
# self.skill_use_count = {k: 0 for k in ACTIVE_SKILLS}
# self.mutated_skills  = set()

# _use_skill 내 추가:
# self.player.skill_use_count[skey] += 1
# threshold = SKILL_MUTATION_DATA.get(skey, {}).get("threshold", 999)
# if self.player.skill_use_count[skey] >= threshold:
#     self._mutate_skill(skey)
```

---

### 🆕 NEW: PASSIVE TRIGGER SKILLS — 조건부 패시브 스킬

**개념:** 쿨타임 없이 특정 상황에서 자동으로 발동되는 스킬 레이어

| 스킬 이름 | 발동 조건 | 효과 |
|---|---|---|
| **LAST STAND** | HP 20% 이하 | 5초간 무적 + 전 주변 적에게 폭발 |
| **VENGEANCE** | 피격 시 (쉴드 0) | 다음 공격 데미지 × 5 (1회) |
| **WARP REFLEX** | 대쉬 직후 0.3초 | 지나친 경로의 적에게 10 데미지 |
| **CHAIN REACTION** | 5킬 콤보 달성 | 탄환이 다음 적에게 자동 유도 (3초) |
| **VOID HUNGER** | VOID 차원 10초 이상 | 탄환 데미지 +50%, 적 슬로우 |

```python
PASSIVE_SKILLS = {
    "last_stand": {
        "name": "라스트 스탠드",
        "trigger": "hp_below_20",
        "cooldown": 1800,   # 30초 (한 판당 2회 정도)
        "desc": "HP 20% 이하 시 자동 발동"
    },
    "vengeance": {
        "name": "복수의 칼날",
        "trigger": "hit_while_no_shield",
        "cooldown": 300,
        "desc": "쉴드 없을 때 피격 → 다음 공격 ×5"
    },
    "warp_reflex": {
        "name": "워프 반사신경",
        "trigger": "after_dash",
        "cooldown": 0,   # 항상 발동 (대쉬마다)
        "desc": "대쉬 경로에 충격파 생성"
    },
    "chain_reaction": {
        "name": "연쇄 반응",
        "trigger": "combo_5",
        "cooldown": 600,
        "desc": "5콤보 달성 시 유도탄 3초"
    },
    "void_hunger": {
        "name": "공허의 굶주림",
        "trigger": "void_duration_600",
        "cooldown": 0,   # 조건 만족 시 항상
        "desc": "VOID 10초 유지 시 버프"
    }
}
```

---

## 🔵 4. 구현 우선순위 & 적용 로드맵

### Phase 1 — 즉시 적용 가능 (엔진 수정 최소)

```
[완료 목표: 1~2일]

1. WavePulse 공격 → anomaly_core, entropy_core에 적용
   - entities.py: Enemy._try_shoot() 내 "wave_pulse" 분기 추가
   - engine.py: self.wave_pulses 리스트 관리 + update/draw

2. DelayedMine → dreadnought_construct 전용
   - entities.py: EnemyMine 클래스 추가 (EnemyProjectile 상속)
   - engine.py: mine 충돌 처리 분리

3. PassiveSkill: warp_reflex (대쉬 후 충격파)
   - engine.py: try_dash() 성공 후 _burst() 데미지 버전
```

### Phase 2 — 중간 난이도 (새 클래스 필요)

```
[완료 목표: 3~5일]

4. EchoShot → sniper_node, echo_wraith에 적용
   - Enemy 클래스에 pos_history 리스트 추가
   - EchoShot 전용 Projectile 서브클래스

5. WeakPoint System → 보스 전체 적용
   - Enemy 클래스에 WeakPoint 인스턴스 추가
   - 충돌 시 크리티컬 판정 로직 분리

6. ResonanceSystem → GameManager에 인스턴스 추가
   - _use_skill() 내 공명 판정 코드 삽입
   - 공명 발동 시 별도 이펙트 함수

7. BurstGauge UI → HUD에 게이지 바 추가
```

### Phase 3 — 고난이도 (설계 변경 필요)

```
[완료 목표: 1주+]

8. CursorLockShot → mouse_world_pos 계산 필요
   - engine.py: mouse_world = mouse_pos + camera_offset 전달

9. AdaptiveArmor → weapon_key를 Projectile에 태그
   - Projectile 생성 시 weapon_key 속성 추가
   - Enemy.take_damage()에 weapon_key 파라미터

10. SkillMutation → owned_skills 저장 구조 확장
    - skill_use_count 저장/로드 (_save_data 수정)
    - 변이 스킬 별도 ACTIVE_SKILLS 딕셔너리
```

---

## 🟣 5. 밸런스 가이드라인

### 신규 적 공격 데미지 기준

| 공격 유형 | 기본 데미지 | 회피 방법 | 난이도 |
|---|---|---|---|
| EchoShot | 10 | 이동 패턴 변칙화 | ★★★ |
| DelayedMine | 18~25 (거리 비례) | 폭발 범위 이탈 | ★★ |
| MirrorBolt | 12 (반사마다 +2) | 벽에서 멀어지기 | ★★★ |
| GravityBolt | 8 (간접 위험) | 빠른 방향 전환 | ★★ |
| WavePulse | 14 (링 두께 통과 시) | 안쪽 or 바깥 | ★★★★ |
| CursorLock | 16 + 가속 | 조준 유인 후 대쉬 | ★★★★★ |
| ChainLightning | 12 → 8 → 5 (감쇄) | 탄환 수 줄이기 | ★★★ |
| VoidAnchor | 고정 효과 (직접 없음) | 대쉬 탈출 | ★★★★ |

### 스킬 공명 데미지 기준

```
기본 스킬 데미지 합산의 2.5배 (상한 500)
공명 발동 시 버스트 게이지 +30%
공명 쿨타임: 두 스킬 중 긴 쿨타임 × 0.5
```

---

## 📋 6. entities.py 수정 체크리스트

```python
# entities.py 최상단에 추가할 클래스 목록

class EchoShotEnemy:         ...  # TYPE-1
class DelayedMine:           ...  # TYPE-2 (EnemyProjectile 상속)
class MirrorBolt:            ...  # TYPE-3 (EnemyProjectile 상속)
class GravityBolt:           ...  # TYPE-4 (EnemyProjectile 상속)
class WavePulse:             ...  # TYPE-5 (스프라이트 아님, 순수 로직)
class CursorLockShot:        ...  # TYPE-6 (EnemyProjectile 상속)
class ChainLightning:        ...  # TYPE-7 (EnemyProjectile 상속)
class VoidAnchorEffect:      ...  # TYPE-8 (Player에 상태 부여)

class WeakPoint:             ...  # MECH-2
class AdaptiveArmor:         ...  # MECH-3
class BurstGauge:            ...  # MECH-4
class DimensionalGhost:      ...  # MECH-1

class ResonanceSystem:       ...  # 스킬 공명
class PassiveTrigger:        ...  # 패시브 스킬 관리자
```

---

*이 문서는 `DIMENSION FIGHT` 전투 시스템 2차 개발을 위한 설계 기반 문서입니다.*
*코드 스니펫은 의사코드 수준으로 실제 통합 시 엔진의 구조에 맞게 조정 필요.*
