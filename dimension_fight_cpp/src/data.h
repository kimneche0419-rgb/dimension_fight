#pragma once
#include "utils.h"
#include <string>
#include <vector>
#include <map>

constexpr int SCREEN_W = 800;
constexpr int SCREEN_H = 600;
constexpr int TARGET_FPS = 60;
constexpr float WORLD_SIZE = 5000.0f;

// ── Dimensions ──
enum class Dimension { PHYSICAL, VOID_DIM };

// ── Game States ──
enum class GameState {
    MENU, COLOR_SELECT, PLAYING, DEATH, WIN,
    SHOP, CRAFTING, GACHA, JOB_SHOP, MULTIPLAYER_LOBBY, SHIP_SHOP
};

// ── Ship Mode ──
enum class ShipMode { SHIP, HUMAN };

// ── Weapon Data ──
struct WeaponData {
    const char* key;
    const char* name;
    int cooldown;
    float speed;
    int dmg;
    Color color_p;
    Color color_v;
    int size;
    int spread;
    int count;
    int unlock_level;
};

inline const std::vector<WeaponData>& getWeapons() {
    static const std::vector<WeaponData> weapons = {
        {"laser",       "P-11 Plasma",       12, 16, 1, {0,255,255},   {255,0,255},   5,  0,  1, 1},
        {"shotgun",     "Void Blitzer",      42, 10, 2, {255,200,0},   {255,100,0},   4,  25, 6, 3},
        {"sniper",      "Continuum Rail",    46, 24, 6, {200,255,200}, {100,255,200}, 3,  0,  1, 5},
        {"gatling",     "Particle Shredder",  6, 11, 1, {255,150,50},  {200,50,255},  4,  10, 1, 8},
        {"rocket",      "Gravity Collapse",  65,  8, 8, {255,80,80},   {180,0,180},   8,  0,  1, 12},
        {"robot_arm",   "Drone Sentinel",    14, 12, 2, {100,200,255}, {200,100,255}, 6,  5,  2, 16},
        {"plasma",      "Solar Radiator",    28,  9, 3, {180,0,255},   {0,255,180},   9,  5,  3, 20},
        {"railgun",     "Omega Railgun",     80, 28,12, {255,255,0},   {255,100,0},   4,  0,  1, 25},
        {"void_cannon", "Abyss Singularity", 45,  7, 5, {80,0,180},    {0,220,255},  12,  0,  1, 30},
        {"abyss_beam",  "High-Pressure Burst",8, 16, 2, {0,80,200},    {200,0,100},   5,  2,  2, 35},
        {"shockwave",   "Nova Impact",       60,  3, 8, {255,180,0},   {0,255,255},  18,  0,  1, 40},
        {"spiral",      "Nebula Spiral",     14, 13, 2, {255,80,200},  {80,255,80},   6,  45, 3, 45},
    };
    return weapons;
}

// ── Enemy Types ──
struct EnemyType {
    const char* key;
    const char* name;
    int hp;
    float speed;
    int size;
    int xp;
    int gold;
    Color color_p;
    Color color_v;
    const char* behavior;  // "chase", "swarm", "zigzag", "orbit", "boss"
    int shoot_cd;          // 0 = doesn't shoot
    Dimension dim;
};

inline const std::vector<EnemyType>& getEnemyTypes() {
    static const std::vector<EnemyType> types = {
        {"drone",       "Drone",          3,  2.0f, 12, 10,  5, {255,100,100}, {255,50,255}, "chase",   0,   Dimension::PHYSICAL},
        {"scout",       "Scout",          5,  3.0f, 10, 15,  8, {255,180,50},  {200,100,255},"zigzag",  0,   Dimension::PHYSICAL},
        {"tank",        "Tank",          15,  1.2f, 22, 30, 15, {200,200,200}, {150,100,200},"chase",   120, Dimension::PHYSICAL},
        {"swarm",       "Swarm",          2,  2.8f,  8,  5,  3, {100,255,100}, {100,200,255},"swarm",   0,   Dimension::PHYSICAL},
        {"sniper",      "Sniper",         8,  1.0f, 14, 25, 12, {255,255,100}, {200,255,100},"orbit",   80,  Dimension::PHYSICAL},
        {"void_drone",  "Void Drone",     4,  2.5f, 12, 12,  6, {180,0,255},   {255,0,180},  "chase",   0,   Dimension::VOID_DIM},
        {"void_hunter", "Void Hunter",   10,  2.0f, 16, 20, 10, {120,0,200},   {200,50,255}, "zigzag",  90,  Dimension::VOID_DIM},
        {"abyss_eel",   "Abyss Eel",      6,  3.5f, 10, 18,  8, {0,150,200},   {0,200,255},  "zigzag",  0,   Dimension::PHYSICAL},
        {"abyss_jelly", "Abyss Jelly",   12,  0.8f, 26, 25, 12, {0,80,180},    {0,120,255},  "chase",   100, Dimension::PHYSICAL},
        {"elite",       "Elite Warrior",  25,  1.8f, 18, 50, 25, {255,50,50},   {255,100,50}, "chase",   60,  Dimension::PHYSICAL},
        {"void_god",    "Void God",      200,  0.5f, 40,500,100, {200,0,255},   {255,50,200}, "boss",    40,  Dimension::VOID_DIM},
        {"abyss_lord",  "Abyss Lord",    150,  0.6f, 36,400, 80, {0,100,255},   {0,200,255},  "boss",    50,  Dimension::PHYSICAL},
    };
    return types;
}

// ── Chapter Data ──
struct ChapterData {
    const char* id;
    const char* name;
    ShipMode mode;
    Color bg_start;
    Color bg_end;
    int duration;      // seconds
    const char* desc;
    const char* enemy_set;  // "normal", "abyss", "void", "all"
};

inline const std::vector<ChapterData>& getChapters() {
    static const std::vector<ChapterData> chapters = {
        {"1", "Sector Zero",    ShipMode::SHIP,  {10,20,30}, {60,5,20},  3600, "Zero-G Combat Training",    "normal"},
        {"2", "Neon Ruins",     ShipMode::HUMAN, {30,30,40}, {50,10,10}, 3600, "Urban Infantry Operations",  "normal"},
        {"3", "Vantablack Deep",ShipMode::SHIP,  {5,30,40},  {0,10,60},  3600, "Deep Sea Flight",           "abyss"},
        {"4", "Event Horizon",  ShipMode::SHIP,  {20,0,40},  {80,0,100}, 3600, "Void Rift",                 "void"},
        {"5", "Singularity",    ShipMode::SHIP,  {40,10,20}, {5,40,50},  3600, "Extreme Difficulty",        "all"},
    };
    return chapters;
}

// ── Item Types ──
enum class ItemType {
    HEALTH, SHIELD, SPEED_BOOST, DAMAGE_BOOST, XP_ORB, DIAMOND,
    BOSS_CORE, VOID_ESSENCE, ABYSS_PEARL, TIME_SHARD
};

struct ItemData {
    ItemType type;
    const char* name;
    Color color;
    float drop_chance;  // weight
};

inline const std::vector<ItemData>& getItems() {
    static const std::vector<ItemData> items = {
        {ItemType::HEALTH,       "Health Pack",  {255,80,80},    30},
        {ItemType::SHIELD,       "Shield Cell",  {80,180,255},   25},
        {ItemType::SPEED_BOOST,  "Speed Boost",  {80,255,80},    15},
        {ItemType::DAMAGE_BOOST, "Damage Amp",   {255,200,50},   10},
        {ItemType::XP_ORB,       "XP Orb",       {200,100,255},  15},
        {ItemType::DIAMOND,      "Diamond",      {100,220,255},   5},
    };
    return items;
}

// ── Levelup Choices ──
enum class LevelupType {
    FIRE_RATE, DAMAGE, MAX_HP, MAX_SHIELD, SPEED, MULTI_SHOT
};

struct LevelupChoice {
    LevelupType type;
    const char* name;
    const char* desc;
};

// ── Ship Colors ──
struct ShipColor {
    const char* name;
    Color body;
    Color accent;
};

inline const std::vector<ShipColor>& getShipColors() {
    static const std::vector<ShipColor> colors = {
        {"Amber",     {255,180,50},  {255,120,0}},
        {"Crimson",   {220,40,40},   {180,0,0}},
        {"Cyan",      {0,220,255},   {0,150,200}},
        {"Emerald",   {50,220,80},   {0,180,50}},
        {"Violet",    {180,80,255},  {120,0,200}},
        {"White",     {240,240,255}, {180,180,200}},
        {"Gold",      {255,215,0},   {200,170,0}},
    };
    return colors;
}

// ── Ship Types ──
struct ShipData {
    const char* key;
    const char* name_ko;
    const char* desc;
    int buy_gold;
    int buy_diamond;
    int buy_pearl;
    int upgrade_gold;   // gold cost per level-up
    int max_level;
    int hp_per_lvl;
    int shield_per_lvl;
    int dmg_pct_per_lvl;    // damage % per level
    int speed_pct_per_lvl;  // speed % per level
    Color color;
    Color accent;
};

inline const std::vector<ShipData>& getShipTypes() {
    static const std::vector<ShipData> ships = {
        //  key          name      desc                          buyG  buyD  buyP  upgG  max  hp  sh  dmg spd  color               accent
        {"fighter",    "전투기",   "기본 전투기. 균형잡힌 성능",       0,    0,    0,    80,  10,  5,  0,  5,  3,  {100,180,255}, {50,120,200}},
        {"cruiser",    "순양함",   "중장갑 전함. 높은 체력과 방어",   500,    0,    0,   150,  10, 20,  8,  3,  0,  {200,160,80},  {140,100,20}},
        {"dreadnought","드레드노트","강력한 화력의 대형 전함",       2000,    0,    0,   250,  10,  8,  0, 15,  0,  {220,80,80},   {160,30,30}},
        {"stealth",    "스텔스",   "고속 기동 전함. 빠른 속도",      1500,    0,    0,   200,  10,  3,  0,  5, 10,  {80,220,180},  {30,160,120}},
        {"abyss_ship", "심해함",   "심해 에너지 전함. 강력한 방어",     0,    0,   30,   200,  10,  5, 15,  8,  2,  {0,120,200},   {0,60,150}},
        {"phantom",    "팬텀",     "공허 전함. 모든 능력치 강화",       0,   50,    0,   300,  10, 10,  5, 10,  6,  {180,80,255},  {100,20,200}},
    };
    return ships;
}

// ── Persistent Upgrades ──
struct UpgradeData {
    const char* key;
    const char* name;
    int cost;
    const char* currency;  // "gold" or "diamond"
    const char* desc;
    int max_lvl;
};

inline const std::vector<UpgradeData>& getUpgrades() {
    static const std::vector<UpgradeData> upgrades = {
        {"shield_boost", "Enhanced Shield",  50,  "gold",    "Max Shield +5", 10},
        {"speed_boost",  "Engine Overclock",100,  "gold",    "Move Speed +3%",10},
        {"hp_boost",     "Hull Reinforce",   80,  "gold",    "Max HP +10",    10},
        {"xp_bonus",     "Neural Link",       5,  "diamond", "XP Gain +5%",    5},
        {"dash_cdr",     "Flux Capacitor",   12,  "diamond", "Dash CDR -5%",  10},
        {"dmg_boost",    "Omega Core",       15,  "diamond", "Damage +10%",    5},
    };
    return upgrades;
}

// ── Anime Fruit System ──
struct RarityInfo {
    const char* label;
    Color color;
    Color glow;
    float rate;
    int max_skills;
};

inline const std::map<std::string, RarityInfo>& getRarityData() {
    static const std::map<std::string, RarityInfo> rarities = {
        {"COMMON",    {"일반",   {180, 180, 180}, {120, 120, 120}, 40.0f, 4}},
        {"UNCOMMON",  {"희귀",   {100, 220, 100}, {60,  180, 100}, 25.0f, 4}},
        {"RARE",      {"레어",   {80,  160, 255}, {40,  100, 255}, 18.0f, 4}},
        {"EPIC",      {"에픽",   {180, 80,  255}, {120, 40,  200}, 10.0f, 4}},
        {"LEGENDARY", {"전설",   {255, 180, 40},  {255, 120, 0},    5.0f, 5}},
        {"MYTHIC",    {"신화",   {255, 60,  120}, {255, 0,   80},   1.5f, 5}},
        {"SECRET",    {"시크릿", {0,   255, 255}, {0,   180, 255},  0.5f, 6}}
    };
    return rarities;
}

struct AnimeSkillData {
    const char* key;
    const char* name;
    const char* series;
    const char* rarity;
    const char* desc;
    int cd;
    int max_lvl;
    const char* type;  // "active", "passive"
    const char* stype; // "active_burst", "active_proj", "active_summon", "active_buff", "active_target"
    int dmg;
    int dmg_scale;
    int range;
    int range_scale;
    Color color;
};

inline const std::map<std::string, AnimeSkillData>& getAnimeSkills() {
    static const std::map<std::string, AnimeSkillData> skills = {
        {"jjk_cursed_strike", {"jjk_cursed_strike", "저주 강타", "주술회전", "COMMON", "저주 에너지를 담은 강력한 타격", 240, 5, "active", "active_burst", 35, 15, 160, 10, {100, 200, 100}}},
        {"jjk_divergent_fist", {"jjk_divergent_fist", "발산권", "주술회전", "UNCOMMON", "시간차 이중 폭발 타격", 360, 5, "active", "active_burst", 55, 20, 180, 12, {60, 255, 160}}},
        {"jjk_curse_slash", {"jjk_curse_slash", "저주 참격", "주술회전", "RARE", "저주 참격 투사체를 날려 적 관통", 420, 5, "active", "active_proj", 75, 25, 18, 2, {80, 220, 140}}},
        {"jjk_black_flash", {"jjk_black_flash", "흑섬", "주술회전", "EPIC", "공간을 왜곡하는 치명적 흑섬 폭발", 600, 5, "active", "active_burst", 120, 45, 220, 15, {30, 30, 80}}},
        {"jjk_ten_shadows", {"jjk_ten_shadows", "십종영법술", "주술회전", "EPIC", "그림자 식신 소환", 800, 5, "active", "active_summon", 0, 0, 0, 0, {50, 50, 50}}},
        {"jjk_hollow_purple", {"jjk_hollow_purple", "허식·자", "주술회전", "LEGENDARY", "가상 질량을 발사하여 전방 소멸", 1200, 5, "active", "active_proj", 200, 60, 25, 3, {180, 80, 255}}},
        {"jjk_infinite_void", {"jjk_infinite_void", "무량공처", "주술회전", "MYTHIC", "영역 전개 - 화면 내 적 완전 정지", 1800, 3, "active", "infinite_void", 0, 0, 0, 0, {0, 200, 255}}},
        {"jjk_sukuna_domain", {"jjk_sukuna_domain", "복마어주자", "주술회전", "SECRET", "끊임없는 참격으로 주변 광폭 초토화", 2400, 3, "active", "active_burst", 450, 150, 450, 50, {200, 30, 30}}},
        {"naruto_clone", {"naruto_clone", "그림자 분신술", "나루토", "COMMON", "분신을 소환하여 협력 전투", 300, 5, "active", "active_summon", 0, 0, 0, 0, {255, 200, 60}}},
        {"naruto_rasengan", {"naruto_rasengan", "나선환", "나루토", "UNCOMMON", "고농축 회전 차크라 구체 발사", 360, 5, "active", "active_proj", 60, 20, 16, 2, {80, 180, 255}}},
        {"naruto_chidori", {"naruto_chidori", "치도리", "나루토", "RARE", "뇌둔을 손끝에 모아 돌격 전격", 420, 5, "active", "active_proj", 80, 25, 20, 2, {200, 230, 255}}},
        {"naruto_amaterasu", {"naruto_amaterasu", "천조", "나루토", "EPIC", "마우스 위치에 꺼지지 않는 흑염 방출", 1000, 5, "active", "active_target", 120, 35, 250, 20, {20, 20, 20}}},
        {"naruto_izanagi", {"naruto_izanagi", "이자나기", "나루토", "EPIC", "사망 시 부활하는 패시브 술법", 3000, 3, "passive", "izanagi", 0, 0, 0, 0, {255, 255, 150}}},
        {"naruto_bijuu_bomb", {"naruto_bijuu_bomb", "미수옥", "나루토", "LEGENDARY", "구미의 미수 구슬 대폭발", 1200, 5, "active", "active_burst", 260, 90, 350, 30, {80, 0, 180}}},
        {"naruto_baryon_mode", {"naruto_baryon_mode", "바리온 모드", "나루토", "MYTHIC", "차크라 융합을 통한 궁극의 버프", 1800, 3, "active", "active_buff", 0, 0, 0, 0, {255, 100, 0}}},
        {"naruto_rinnegan_meteor", {"naruto_rinnegan_meteor", "천애진성", "나루토", "SECRET", "거대 운석을 낙하시켜 초광역 피해", 2400, 3, "active", "active_target", 520, 180, 480, 40, {255, 50, 0}}},
        {"aot_mobility", {"aot_mobility", "입체기동 장치", "진격의거인", "COMMON", "대쉬 쿨타임을 초기화하는 기동술", 10, 5, "passive", "mobility", 0, 0, 0, 0, {180, 160, 120}}},
        {"aot_thunder_spear", {"aot_thunder_spear", "뇌창", "진격의거인", "UNCOMMON", "지연 폭발식 대거인 병기 발사", 400, 5, "active", "active_proj", 150, 45, 15, 2, {160, 180, 180}}},
        {"aot_hardening", {"aot_hardening", "경화 능력", "진격의거인", "RARE", "선체를 경화하여 이속/방어 상승", 500, 5, "active", "active_buff", 0, 0, 0, 0, {100, 80, 40}}},
        {"aot_titan_form", {"aot_titan_form", "거인화", "진격의거인", "EPIC", "거인화하여 밟기 폭발 데미지 유발", 1500, 5, "active", "titan_form", 250, 80, 300, 25, {180, 120, 60}}},
        {"aot_war_hammer", {"aot_war_hammer", "전퇴의 망치", "진격의거인", "LEGENDARY", "결정 대지를 융기시켜 범위 관통 폭사", 1000, 5, "active", "active_target", 220, 60, 300, 25, {220, 200, 255}}},
        {"aot_colossal_steam", {"aot_colossal_steam", "초대형 증기", "진격의거인", "MYTHIC", "초고열 증기를 뿜어 광역 지속 피해", 1600, 3, "active", "active_burst", 320, 100, 400, 35, {255, 100, 50}}},
        {"aot_rumbling", {"aot_rumbling", "지명 (땅울림)", "진격의거인", "SECRET", "수많은 벽거인들을 해방하여 대지 소멸", 2400, 3, "active", "active_target", 580, 200, 550, 50, {100, 20, 20}}},
        {"slev_arise", {"slev_arise", "어라이즈", "나혼렙", "COMMON", "그림자 보조병을 즉시 소환", 240, 5, "active", "active_summon", 0, 0, 0, 0, {60, 60, 80}}},
        {"slev_shadow_exchange", {"slev_shadow_exchange", "그림자 교환", "나혼렙", "UNCOMMON", "순간 속도 증폭 버프", 300, 5, "active", "active_buff", 0, 0, 0, 0, {40, 40, 100}}},
        {"slev_shadow_extract", {"slev_shadow_extract", "그림자 추출", "나혼렙", "RARE", "강력한 그림자 군단 소환", 800, 5, "active", "active_summon", 0, 0, 0, 0, {40, 40, 100}}},
        {"slev_steel_body", {"slev_steel_body", "강철 몸체", "나혼렙", "EPIC", "선체 강화 버프 제공", 900, 5, "active", "active_buff", 0, 0, 0, 0, {100, 140, 180}}},
        {"slev_hunter_instinct", {"slev_hunter_instinct", "헌터의 직감", "나혼렙", "LEGENDARY", "공격 속도 및 공격력 동시 대폭 버프", 1200, 5, "active", "active_buff", 0, 0, 0, 0, {200, 50, 50}}},
        {"slev_monarch", {"slev_monarch", "그림자 군주", "나혼렙", "MYTHIC", "다수의 엘리트 그림자 병사 소환", 1800, 3, "active", "active_summon", 0, 0, 0, 0, {80, 0, 160}}},
        {"slev_absolute_power", {"slev_absolute_power", "절대자의 지배", "나혼렙", "SECRET", "지배자의 권능으로 광역 파괴 서지 유발", 2400, 3, "active", "active_burst", 480, 160, 450, 45, {0, 255, 255}}},
        {"op_gum_pistol", {"op_gum_pistol", "고무고무 피스톨", "원피스", "COMMON", "고무 주먹 투사체 발사", 200, 5, "active", "active_proj", 40, 12, 15, 1, {255, 180, 100}}},
        {"op_chop_chop", {"op_chop_chop", "동강동강 회피", "원피스", "UNCOMMON", "즉시 고속 이동 버프", 260, 5, "active", "active_buff", 0, 0, 0, 0, {255, 120, 255}}},
        {"op_smoke_blow", {"op_smoke_blow", "화이트 아웃", "원피스", "RARE", "연기 폭풍을 뿜어 광역 데미지", 360, 5, "active", "active_burst", 65, 18, 200, 15, {220, 220, 220}}},
        {"op_fire_fist", {"op_fire_fist", "불건 (화권)", "원피스", "EPIC", "거대한 화염 참격을 마우스 방향 사격", 480, 5, "active", "active_proj", 120, 40, 26, 3, {255, 80, 0}}},
        {"op_tremor", {"op_tremor", "흔들흔들 격진", "원피스", "LEGENDARY", "공간을 깨부수는 초강력 파괴 진동", 1000, 5, "active", "active_burst", 230, 70, 350, 30, {255, 255, 255}}},
        {"op_gear5", {"op_gear5", "태양신 니카 (기어5)", "원피스", "MYTHIC", "공격력/속도 극대화 버프", 1800, 3, "active", "active_buff", 0, 0, 0, 0, {255, 255, 180}}},
        {"op_haki_king", {"op_haki_king", "패왕색 패기", "원피스", "SECRET", "패왕의 기백으로 전 화면 적 즉시 타격", 2400, 3, "active", "active_burst", 480, 160, 520, 50, {150, 0, 255}}},
        {"ds_water_slash", {"ds_water_slash", "수면 베기", "귀멸의칼날", "COMMON", "물의 흐름을 담은 사선 베기 투사체", 220, 5, "active", "active_proj", 45, 12, 16, 1, {0, 150, 255}}},
        {"ds_thunder_clap", {"ds_thunder_clap", "벽력일섬", "귀멸의칼날", "UNCOMMON", "광속 번개 돌진 투사체 사격", 280, 5, "active", "active_proj", 65, 20, 18, 2, {255, 255, 0}}},
        {"ds_beast_fang", {"ds_beast_fang", "공간참 베기", "귀멸의칼날", "RARE", "짐승의 칼날로 교차 사격 충격파", 360, 5, "active", "active_burst", 75, 22, 210, 15, {100, 200, 200}}},
        {"ds_flame_tiger", {"ds_flame_tiger", "염호 (불꽃의 호흡)", "귀멸의칼날", "EPIC", "전방으로 돌진하는 거대 불꽃 호랑이 발사", 500, 5, "active", "active_proj", 125, 38, 25, 3, {255, 50, 0}}},
        {"ds_sun_halo", {"ds_sun_halo", "푸른 하늘 (원무)", "귀멸의칼날", "LEGENDARY", "해의 호흡 춤으로 주변 적 일제 섬멸", 1000, 5, "active", "active_burst", 240, 75, 330, 30, {255, 100, 0}}},
        {"ds_blue_spider", {"ds_blue_spider", "피안화의 소용돌이", "귀멸의칼날", "MYTHIC", "푸른 피안화의 폭풍으로 화면 전체 피해", 1600, 3, "active", "active_target", 360, 110, 420, 40, {0, 100, 255}}},
        {"ds_muzans_blood", {"ds_muzans_blood", "무잔의 채찍", "귀멸의칼날", "SECRET", "혈귀술 가시 촉수로 주변 광역 파괴", 2400, 3, "active", "active_burst", 500, 170, 500, 50, {120, 0, 0}}},
        {"bl_soul_strike", {"bl_soul_strike", "참격", "블리치", "COMMON", "사신의 푸른 영압 참격 발사", 200, 5, "active", "active_proj", 40, 12, 15, 1, {200, 200, 255}}},
        {"bl_shikai", {"bl_shikai", "시해 해방", "블리치", "UNCOMMON", "일시 공격력 강화 버프", 300, 5, "active", "active_buff", 0, 0, 0, 0, {150, 150, 250}}},
        {"bl_getsuga", {"bl_getsuga", "월아천충", "블리치", "RARE", "참월의 흑색 에너지 방출격", 500, 5, "active", "active_proj", 160, 40, 20, 2, {30, 30, 50}}},
        {"bl_hollowify", {"bl_hollowify", "호로화", "블리치", "EPIC", "가면 해방 - 이속/뎀증 대량 버프", 900, 5, "active", "active_buff", 0, 0, 0, 0, {255, 0, 100}}},
        {"bl_hogyoku", {"bl_hogyoku", "붕옥의 진화", "블리치", "LEGENDARY", "경계를 허물어 압도적 초월 버프", 1200, 5, "active", "active_buff", 0, 0, 0, 0, {0, 255, 200}}},
        {"bl_ryujin_jakka", {"bl_ryujin_jakka", "잔화태도", "블리치", "MYTHIC", "온 대지를 불태우는 열옥 폭발", 1800, 3, "active", "active_burst", 380, 120, 400, 40, {255, 60, 0}}},
        {"bl_mugetsu", {"bl_mugetsu", "무월 (無月)", "블리치", "SECRET", "최후의 월아천충 - 전 화면 칠흑의 소멸격", 2400, 3, "active", "active_burst", 620, 210, 580, 60, {10, 10, 15}}},
        {"db_ki_blast", {"db_ki_blast", "기공파", "드래곤볼", "COMMON", "기와 에너지를 모아 구체탄 발사", 210, 5, "active", "active_proj", 45, 14, 16, 1, {255, 255, 150}}},
        {"db_kaioken", {"db_kaioken", "계왕권", "드래곤볼", "UNCOMMON", "기동성 극대화 버프", 320, 5, "active", "active_buff", 0, 0, 0, 0, {255, 50, 50}}},
        {"db_spirit_bomb", {"db_spirit_bomb", "원기옥", "드래곤볼", "RARE", "생명체의 원기를 모아 광역 지점 강타", 500, 5, "active", "active_target", 110, 35, 260, 20, {100, 150, 255}}},
        {"db_super_saiyan", {"db_super_saiyan", "초사이어인", "드래곤볼", "EPIC", "금빛 전사 각성 버프 - 공격력/속도 강화", 900, 5, "active", "active_buff", 0, 0, 0, 0, {255, 215, 0}}},
        {"db_kamehameha", {"db_kamehameha", "에네르기파", "드래곤볼", "LEGENDARY", "두 손에 모은 대출력 에너지파 발사", 1100, 5, "active", "active_proj", 260, 85, 30, 4, {0, 191, 255}}},
        {"db_ui", {"db_ui", "무의식의 극의", "드래곤볼", "MYTHIC", "회피 및 뎀증 신급 버프", 1800, 3, "active", "active_buff", 0, 0, 0, 0, {240, 240, 255}}},
        {"db_shenron", {"db_shenron", "신룡의 분노", "드래곤볼", "SECRET", "소환된 신룡이 전 방향 우주적 기운 방출", 2400, 3, "active", "active_burst", 580, 190, 550, 50, {0, 255, 100}}}
    };
    return skills;
}

struct AnimeFruitData {
    const char* key;
    const char* name;
    const char* series;
    const char* rarity;
    const char* desc;
    std::vector<std::string> skills;
    Color color;
    const char* icon;
};

inline const std::map<std::string, AnimeFruitData>& getAnimeFruits() {
    static const std::map<std::string, AnimeFruitData> fruits = {
        {"jjk_common", {"jjk_common", "저주의 씨앗", "주술회전", "COMMON", "저급 저주 에너지가 깃든 씨앗", {"jjk_cursed_strike", "jjk_divergent_fist", "jjk_curse_slash", "jjk_black_flash"}, {100, 200, 100}, "🌿"}},
        {"jjk_uncommon", {"jjk_uncommon", "식신의 열매", "주술회전", "UNCOMMON", "그림자 식신의 기운이 담긴 열매", {"jjk_cursed_strike", "jjk_divergent_fist", "jjk_curse_slash", "jjk_ten_shadows"}, {120, 220, 120}, "🐕"}},
        {"jjk_rare", {"jjk_rare", "반전 술식의 열매", "주술회전", "RARE", "반전 주술의 깨달음이 모인 결정체", {"jjk_divergent_fist", "jjk_curse_slash", "jjk_black_flash", "jjk_ten_shadows"}, {80, 220, 140}, "💚"}},
        {"jjk_epic", {"jjk_epic", "흑섬의 열매", "주술회전", "EPIC", "흑섬의 저주 에너지가 고속 충돌한 결정", {"jjk_cursed_strike", "jjk_divergent_fist", "jjk_curse_slash", "jjk_black_flash", "jjk_ten_shadows"}, {30, 30, 80}, "⬛"}},
        {"jjk_legendary", {"jjk_legendary", "천역모의 열매", "주술회전", "LEGENDARY", "주력을 무효화하는 천역모의 마법 열매", {"jjk_curse_slash", "jjk_black_flash", "jjk_ten_shadows", "jjk_hollow_purple", "jjk_infinite_void"}, {180, 80, 255}, "🗡"}},
        {"jjk_mythic", {"jjk_mythic", "무량공처의 열매", "주술회전", "MYTHIC", "영역 전개 능력이 깃든 최강 열매", {"jjk_divergent_fist", "jjk_curse_slash", "jjk_black_flash", "jjk_ten_shadows", "jjk_hollow_purple", "jjk_infinite_void"}, {0, 200, 255}, "∞"}},
        {"jjk_secret", {"jjk_secret", "양면 스쿠나의 손가락", "주술회전", "SECRET", "저주의 왕 스쿠나의 파괴력이 깃든 봉인구", {"jjk_cursed_strike", "jjk_divergent_fist", "jjk_curse_slash", "jjk_black_flash", "jjk_hollow_purple", "jjk_infinite_void", "jjk_sukuna_domain"}, {200, 30, 30}, "👹"}},
        {"naruto_common", {"naruto_common", "차크라의 씨앗", "나루토", "COMMON", "기초 닌자 차크라가 담긴 씨앗", {"naruto_clone", "naruto_rasengan", "naruto_chidori", "naruto_amaterasu"}, {255, 200, 60}, "🌀"}},
        {"naruto_uncommon", {"naruto_uncommon", "백안의 열매", "나루토", "UNCOMMON", "휴가 일족의 3대 동술인 백안의 안력", {"naruto_clone", "naruto_rasengan", "naruto_chidori", "naruto_izanagi"}, {220, 240, 255}, "👁"}},
        {"naruto_rare", {"naruto_rare", "나선환의 열매", "나루토", "RARE", "강력한 나선 차크라가 깃든 결정체", {"naruto_rasengan", "naruto_chidori", "naruto_amaterasu", "naruto_izanagi"}, {80, 180, 255}, "🔵"}},
        {"naruto_epic", {"naruto_epic", "만화경 사륜안의 열매", "나루토", "EPIC", "우치하 일족의 눈동자가 깃든 열매", {"naruto_clone", "naruto_rasengan", "naruto_chidori", "naruto_amaterasu", "naruto_izanagi"}, {20, 20, 20}, "👁"}},
        {"naruto_legendary", {"naruto_legendary", "구미 차크라의 열매", "나루토", "LEGENDARY", "구미 봉인의 붉은 폭발 에너지가 깃든 열매", {"naruto_chidori", "naruto_amaterasu", "naruto_izanagi", "naruto_bijuu_bomb", "naruto_baryon_mode"}, {255, 120, 0}, "🦊"}},
        {"naruto_mythic", {"naruto_mythic", "바리온 모드의 열매", "나루토", "MYTHIC", "나루토와 쿠라마의 생명력 융합 열매", {"naruto_rasengan", "naruto_chidori", "naruto_amaterasu", "naruto_bijuu_bomb", "naruto_baryon_mode", "naruto_rinnegan_meteor"}, {255, 80, 0}, "☢"}},
        {"naruto_secret", {"naruto_secret", "육도선인의 열매", "나루토", "SECRET", "닌자의 시조인 육도선인의 힘이 깃든 열매", {"naruto_clone", "naruto_rasengan", "naruto_chidori", "naruto_amaterasu", "naruto_bijuu_bomb", "naruto_baryon_mode", "naruto_rinnegan_meteor"}, {255, 255, 150}, "☸"}},
        {"aot_common", {"aot_common", "입체기동 장치 씨앗", "진격의거인", "COMMON", "조사병단 기본 전술이 각인된 씨앗", {"aot_mobility", "aot_thunder_spear", "aot_hardening", "aot_titan_form"}, {180, 160, 120}, "🪝"}},
        {"aot_uncommon", {"aot_uncommon", "거인화 약물 주사기", "진격의거인", "UNCOMMON", "척수액 기반의 거인화 주사기", {"aot_mobility", "aot_thunder_spear", "aot_hardening", "aot_war_hammer"}, {160, 180, 180}, "💉"}},
        {"aot_rare", {"aot_rare", "여성형 거인의 열매", "진격의거인", "RARE", "경화 및 범용 격투술 능력이 깃든 거인 구체", {"aot_thunder_spear", "aot_hardening", "aot_titan_form", "aot_war_hammer"}, {255, 180, 180}, "👱"}},
        {"aot_epic", {"aot_epic", "갑옷 거인의 열매", "진격의거인", "EPIC", "전신이 단단한 갑각 피부로 둘러싸인 거인 구체", {"aot_mobility", "aot_thunder_spear", "aot_hardening", "aot_titan_form", "aot_war_hammer"}, {180, 120, 60}, "🧱"}},
        {"aot_legendary", {"aot_legendary", "초대형 거인의 열매", "진격의거인", "LEGENDARY", "60m의 거대한 신체와 폭발 증기 열매", {"aot_hardening", "aot_titan_form", "aot_war_hammer", "aot_colossal_steam", "aot_rumbling"}, {255, 100, 50}, "🔥"}},
        {"aot_mythic", {"aot_mythic", "시조 거인의 열매", "진격의거인", "MYTHIC", "모든 거인을 지배하는 좌표의 시조 힘", {"aot_thunder_spear", "aot_hardening", "aot_titan_form", "aot_war_hammer", "aot_colossal_steam", "aot_rumbling"}, {200, 50, 50}, "👑"}},
        {"aot_secret", {"aot_secret", "땅울림 시조 에렌", "진격의거인", "SECRET", "수천만 대군 벽거인들을 조종하는 멸망의 열매", {"aot_mobility", "aot_thunder_spear", "aot_hardening", "aot_titan_form", "aot_war_hammer", "aot_colossal_steam", "aot_rumbling"}, {100, 20, 20}, "🌋"}},
        {"slev_common", {"slev_common", "E급 헌터의 씨앗", "나혼렙", "COMMON", "최약병기 인류 헌터의 미약한 씨앗", {"slev_arise", "slev_shadow_exchange", "slev_shadow_extract", "slev_steel_body"}, {60, 60, 80}, "💀"}},
        {"slev_uncommon", {"slev_uncommon", "카르테논 신전의 조각", "나혼렙", "UNCOMMON", "이중 던전의 참혹한 신전 기운 조각", {"slev_arise", "slev_shadow_exchange", "slev_shadow_extract", "slev_hunter_instinct"}, {80, 80, 100}, "🗿"}},
        {"slev_rare", {"slev_rare", "그림자 파편 열매", "나혼렙", "RARE", "그림자 군주의 어두운 마력이 응결된 파편", {"slev_shadow_exchange", "slev_shadow_extract", "slev_steel_body", "slev_hunter_instinct"}, {40, 40, 100}, "🌑"}},
        {"slev_epic", {"slev_epic", "국가급 헌터의 열매", "나혼렙", "EPIC", "세계 5대 국가급 헌터의 에센스 스톤", {"slev_arise", "slev_shadow_exchange", "slev_shadow_extract", "slev_steel_body", "slev_hunter_instinct"}, {100, 140, 180}, "🔩"}},
        {"slev_legendary", {"slev_legendary", "지배자의 권능 열매", "나혼렙", "LEGENDARY", "지배자 광휘의 파편이 깃든 열매", {"slev_shadow_extract", "slev_steel_body", "slev_hunter_instinct", "slev_monarch", "slev_absolute_power"}, {220, 220, 220}, "💎"}},
        {"slev_mythic", {"slev_mythic", "그림자 군주 성진우", "나혼렙", "MYTHIC", "성진우의 모든 군주 소환술이 각성한 결정", {"slev_shadow_exchange", "slev_shadow_extract", "slev_steel_body", "slev_hunter_instinct", "slev_monarch", "slev_absolute_power"}, {80, 0, 160}, "👑"}},
        {"slev_secret", {"slev_secret", "절대자의 푸른 심장", "나혼렙", "SECRET", "무한한 우주적 에너지를 가진 절대자의 영혼석", {"slev_arise", "slev_shadow_exchange", "slev_shadow_extract", "slev_steel_body", "slev_hunter_instinct", "slev_monarch", "slev_absolute_power"}, {0, 255, 255}, "💙"}},
        {"op_common", {"op_common", "고무고무 열매", "원피스", "COMMON", "온몸이 고무처럼 신축 변형되는 열매", {"op_gum_pistol", "op_chop_chop", "op_smoke_blow", "op_fire_fist"}, {255, 180, 100}, "👒"}},
        {"op_uncommon", {"op_uncommon", "동강동강 열매", "원피스", "UNCOMMON", "참격에 면역력을 제공하는 분리 열매", {"op_gum_pistol", "op_chop_chop", "op_smoke_blow", "op_tremor"}, {255, 120, 255}, "🔴"}},
        {"op_rare", {"op_rare", "뭉게뭉게 열매", "원피스", "RARE", "몸을 안개로 바꾸는 연기 열매", {"op_chop_chop", "op_smoke_blow", "op_fire_fist", "op_tremor"}, {220, 220, 220}, "💨"}},
        {"op_epic", {"op_epic", "이글이글 열매", "원피스", "EPIC", "몸을 불꽃으로 변하게 하는 에이스의 화염 열매", {"op_gum_pistol", "op_chop_chop", "op_smoke_blow", "op_fire_fist", "op_tremor"}, {255, 80, 0}, "🔥"}},
        {"op_legendary", {"op_legendary", "흔들흔들 열매", "원피스", "LEGENDARY", "지진 열매", {"op_smoke_blow", "op_fire_fist", "op_tremor", "op_gear5", "op_haki_king"}, {240, 240, 240}, "🌊"}},
        {"op_mythic", {"op_mythic", "고무고무 열매 (니카)", "원피스", "MYTHIC", "해방의 전사 조이보이 니카가 각성한 열매", {"op_chop_chop", "op_smoke_blow", "op_fire_fist", "op_tremor", "op_gear5", "op_haki_king"}, {255, 255, 180}, "☀️"}},
        {"op_secret", {"op_secret", "해적왕의 보물원", "원피스", "SECRET", "골 D. 로저의 전설적인 의지가 깃든 열매", {"op_gum_pistol", "op_chop_chop", "op_smoke_blow", "op_fire_fist", "op_tremor", "op_gear5", "op_haki_king"}, {150, 0, 255}, "🏴‍☠️"}},
        {"ds_common", {"ds_common", "물의 호흡 비법", "귀멸의칼날", "COMMON", "귀살대 기초 호흡 훈련법", {"ds_water_slash", "ds_thunder_clap", "ds_beast_fang", "ds_flame_tiger"}, {0, 150, 255}, "🌊"}},
        {"ds_uncommon", {"ds_uncommon", "번개의 호흡 비법", "귀멸의칼날", "UNCOMMON", "순식간에 적을 베는 일섬 호흡서", {"ds_water_slash", "ds_thunder_clap", "ds_beast_fang", "ds_sun_halo"}, {255, 255, 50}, "⚡"}},
        {"ds_rare", {"ds_rare", "짐승의 호흡 돌검", "귀멸의칼날", "RARE", "야생 짐승의 투박하고 날카로운 야성", {"ds_thunder_clap", "ds_beast_fang", "ds_flame_tiger", "ds_sun_halo"}, {100, 200, 200}, "🐗"}},
        {"ds_epic", {"ds_epic", "불꽃의 호흡 심장", "귀멸의칼날", "EPIC", "렌고쿠 쿄쥬로의 마음을 불태우는 붉은 열매", {"ds_water_slash", "ds_thunder_clap", "ds_beast_fang", "ds_flame_tiger", "ds_sun_halo"}, {255, 30, 30}, "🔥"}},
        {"ds_legendary", {"ds_legendary", "해의 호흡 귀걸이", "귀멸의칼날", "LEGENDARY", "해의 호흡 결정", {"ds_beast_fang", "ds_flame_tiger", "ds_sun_halo", "ds_blue_spider", "ds_muzans_blood"}, {255, 120, 0}, "🎴"}},
        {"ds_mythic", {"ds_mythic", "푸른 피안화의 열매", "귀멸의칼날", "MYTHIC", "환상의 푸른 꽃 열매", {"ds_thunder_clap", "ds_beast_fang", "ds_flame_tiger", "ds_sun_halo", "ds_blue_spider", "ds_muzans_blood"}, {0, 100, 255}, "🌸"}},
        {"ds_secret", {"ds_secret", "천년 시조 키부츠지 무잔", "귀멸의칼날", "SECRET", "도깨비의 왕 무잔의 촉수 혈귀술", {"ds_water_slash", "ds_thunder_clap", "ds_beast_fang", "ds_flame_tiger", "ds_sun_halo", "ds_blue_spider", "ds_muzans_blood"}, {120, 0, 0}, "🩸"}},
        {"bl_common", {"bl_common", "천쇄참월 씨앗", "블리치", "COMMON", "사신의 힘을 깨워주는 작은 영혼의 씨앗", {"bl_soul_strike", "bl_shikai", "bl_getsuga", "bl_hollowify"}, {200, 200, 255}, "⚔"}},
        {"bl_uncommon", {"bl_uncommon", "참백도 혼백", "블리치", "UNCOMMON", "사신의 참백도 혼백", {"bl_soul_strike", "bl_shikai", "bl_getsuga", "bl_hogyoku"}, {150, 150, 250}, "🗡"}},
        {"bl_rare", {"bl_rare", "천쇄참월의 열매", "블리치", "RARE", "흑색 만해 영압이 서린 열매", {"bl_shikai", "bl_getsuga", "bl_hollowify", "bl_hogyoku"}, {30, 30, 50}, "🌑"}},
        {"bl_epic", {"bl_epic", "호로화의 가면", "블리치", "EPIC", "폭주하는 내면의 호로 가면 마스크", {"bl_soul_strike", "bl_shikai", "bl_getsuga", "bl_hollowify", "bl_hogyoku"}, {255, 30, 100}, "🎭"}},
        {"bl_legendary", {"bl_legendary", "붕옥의 진화핵", "블리치", "LEGENDARY", "붕옥의 진화핵", {"bl_getsuga", "bl_hollowify", "bl_hogyoku", "bl_ryujin_jakka", "bl_mugetsu"}, {0, 255, 200}, "🔮"}},
        {"bl_mythic", {"bl_mythic", "잔화태도 류인약화", "블리치", "MYTHIC", "온 대지를 불태우는 열옥 폭발", {"bl_shikai", "bl_getsuga", "bl_hollowify", "bl_hogyoku", "bl_ryujin_jakka", "bl_mugetsu"}, {255, 60, 0}, "🌋"}},
        {"bl_secret", {"bl_secret", "초월자 무월 이치고", "블리치", "SECRET", "사신 그 자체가 되는 궁극의 무월", {"bl_soul_strike", "bl_shikai", "bl_getsuga", "bl_hollowify", "bl_hogyoku", "bl_ryujin_jakka", "bl_mugetsu"}, {10, 10, 15}, "🌌"}},
        {"db_common", {"db_common", "무술대회 단환", "드래곤볼", "COMMON", "무투가의 영력이 깃든 파란 단환", {"db_ki_blast", "db_kaioken", "db_spirit_bomb", "db_super_saiyan"}, {255, 255, 120}, "🥋"}},
        {"db_uncommon", {"db_uncommon", "계왕의 씨앗", "드래곤볼", "UNCOMMON", "계왕성에서 가져온 붉은 씨앗", {"db_ki_blast", "db_kaioken", "db_spirit_bomb", "db_kamehameha"}, {255, 80, 80}, "🐒"}},
        {"db_rare", {"db_rare", "선두의 열매", "드래곤볼", "RARE", "에너지를 회복해 주는 선두", {"db_kaioken", "db_spirit_bomb", "db_super_saiyan", "db_kamehameha"}, {100, 220, 100}, "💚"}},
        {"db_epic", {"db_epic", "초사이어인의 불꽃", "드래곤볼", "EPIC", "금빛 전사로 각성하는 불꽃", {"db_ki_blast", "db_kaioken", "db_spirit_bomb", "db_super_saiyan", "db_kamehameha"}, {255, 215, 0}, "🔥"}},
        {"db_legendary", {"db_legendary", "에네르기파 비결", "드래곤볼", "LEGENDARY", "에네르기파 비결서", {"db_spirit_bomb", "db_super_saiyan", "db_kamehameha", "db_ui", "db_shenron"}, {0, 200, 255}, "☄️"}},
        {"db_mythic", {"db_mythic", "무의식의 극의 구체", "드래곤볼", "MYTHIC", "무의식의 극의 힘 구체", {"db_kaioken", "db_spirit_bomb", "db_super_saiyan", "db_kamehameha", "db_ui", "db_shenron"}, {230, 230, 250}, "🌌"}},
        {"db_secret", {"db_secret", "소환된 우주 신룡", "드래곤볼", "SECRET", "7개 드래곤볼 소환된 신룡", {"db_ki_blast", "db_kaioken", "db_spirit_bomb", "db_super_saiyan", "db_kamehameha", "db_ui", "db_shenron"}, {0, 255, 100}, "🐉"}}
    };
    return fruits;
}

struct CraftingRecipe {
    const char* key;
    const char* name;
    const char* icon;
    int boss_core;
    int void_essence;
    int abyss_pearl;
    int time_shard;
    const char* desc;
    Color color;
};

inline const std::vector<CraftingRecipe>& getCraftingRecipes() {
    static const std::vector<CraftingRecipe> recipes = {
        {"drone_laser", "드론 레이저 모듈", "💜", 1, 1, 0, 0, "드론이 관통 레이저를 발사 / 드론 공격력+50% / 속도+40%", {180, 80, 255}},
        {"time_barrier", "시공간 배리어", "🛡️", 1, 0, 0, 2, "HP 30% 이하 시 3초 무적 자동 발동 (쿨타임 120초)", {0, 200, 255}},
        {"warp_engine", "시공간 기동 엔진", "🔥", 1, 2, 0, 0, "대쉬 쿨타임 50% 감소 / 대쉬 시 화염 궤적 데미지", {255, 120, 0}},
        {"fusion", "핵융합 런처", "☢️", 2, 2, 0, 0, "전설 무기 '핵융합 런처' 영구 해금 / 거대 플라즈마 광역 폭발", {255, 60, 200}},
        {"rift_gauntlet", "차원 균열 건틀릿", "🌌", 2, 0, 0, 2, "차원 전환 시 강력한 차원 파장 발출, 주변 탄환 소멸 및 180 데미지, 1.5초 무적", {150, 50, 255}},
        {"nanobot_pylon", "나노봇 파이론", "⚡", 1, 0, 2, 0, "10초마다 쉴드를 15 회복시키고 주변 적에게 50 전자기 데미지", {0, 255, 255}},
        {"singularity_magnet", "싱귤래리티 마그넷", "🧲", 2, 2, 0, 0, "적 처치 시 20% 확률로 자원을 강하게 끌어당기는 소형 블랙홀 생성", {200, 80, 255}},
        {"photon_shield", "포톤 리플렉터", "💎", 1, 0, 2, 0, "피격 시 30% 확률로 1.5초 무적 상태가 되며 데미지 무효화 및 200% 반사", {255, 200, 50}},
        {"void_hyperdrive", "공허 초광속 엔진", "🚀", 2, 3, 0, 0, "체력 100%일 때 공격 속도 +40% 및 대쉬 시 무적 상태 2초 유지", {50, 255, 100}},
        {"abyssal_orb", "심연의 보주", "🌑", 2, 0, 3, 0, "쉴드 매초 +2 재생. 쉴드 파괴 시 주변 적을 1.5초간 빙결시킴", {0, 120, 255}},
        {"void_crown", "공허의 왕관", "👑", 2, 3, 0, 0, "스킬 시전 시 25% 확률로 쿨타임 초기화 (ICD 15초) 및 공허 데미지 +30%", {180, 0, 255}},
        {"time_chronograph", "시공간 크로노그래프", "⌛", 2, 0, 0, 3, "사망 방지: 치명적 피격 시 체력 50%로 역행, 탄환 제거 및 3초 무적 (쿨 180초)", {255, 220, 50}},
        {"multiverse_matrix", "멀티버스 매트릭스", "🌀", 3, 2, 2, 2, "모든 무기 공격력/연사력 +15%. 차원 전환 시 4초간 이동 속도 +50% 증가", {0, 255, 150}},
        {"nano_techpack", "나노 테크 팩", "🤖", 2, 0, 3, 2, "기본 드론 수 +1 및 소환체 공격력 +30% 증가", {0, 255, 255}}
    };
    return recipes;
}

struct JobData {
    const char* key;
    const char* name;
    const char* job_class;
    const char* desc;
    const char* req_label;
    const char* buff;
    const char* nerf;
    float hp_mult;
    float dmg_mult;
    float speed_mult;
    float shield_mult;
    float cd_mult;
    float skill_cd_mult;
    float skill_dmg_mult;
    float void_dmg_mult;
    bool double_dash;
    bool void_immune;
    float combo_mult_bonus;
    int lifesteal_bonus;
    float gold_mult_bonus;
    float potion_heal_bonus;
    Color color;
};

inline const std::map<std::string, JobData>& getJobData() {
    static const std::map<std::string, JobData> jobs = {
        // 돌격형
        {"전사", {"전사", "전사", "돌격형", "근접 전투의 달인. 두꺼운 장갑으로 전선을 지킨다.", "근접 처치", "최대 HP +35% · 데미지 +20%", "이동속도 -15%", 1.35f, 1.20f, 0.85f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 0, 0.0f, 0.0f, {220, 80, 60}}},
        {"탱커", {"탱커", "탱커", "돌격형", "강철 같은 방어력으로 모든 공격을 버텨낸다.", "피해 받음", "최대 HP +60% · 쉴드 +100%", "이동속도 -30%", 1.60f, 1.00f, 0.70f, 2.0f, 1.0f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 0, 0.0f, 0.0f, {100, 100, 200}}},
        {"학살자", {"학살자", "학살자", "돌격형", "피와 광기로 전장을 물든다. 콤보가 힘이다.", "최고 콤보", "콤보 보너스 2배 · 5킬마다 속도 +5%", "쉴드 없음 · HP -15%", 0.85f, 1.00f, 1.00f, 0.0f, 1.0f, 1.0f, 1.0f, 1.0f, false, false, 2.0f, 0, 0.0f, 0.0f, {255, 100, 0}}},
        // 사격형
        {"저격수", {"저격수", "저격수", "사격형", "먼 거리에서 치명적인 일격을 날린다.", "원거리 처치", "데미지 +50% · 탄속 +25%", "이동속도 -20% · HP -10%", 0.90f, 1.50f, 0.80f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 0, 0.0f, 0.0f, {80, 220, 255}}},
        {"기계공", {"기계공", "기계공", "사격형", "무기 운용의 달인. 모든 무기를 최적화한다.", "무기 전환", "전체 데미지 +15% · 사격속도 +20%", "이동속도 -10%", 1.00f, 1.15f, 0.90f, 1.0f, 0.80f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 0, 0.0f, 0.0f, {200, 180, 80}}},
        {"포격수", {"포격수", "포격수", "사격형", "강력한 화력과 광역 폭발로 적들을 휩쓴다.", "직업 상점 해금", "데미지 +30% · 탄환 크기 +50%", "무기 쿨타임 +20% · 이동속도 -15%", 1.00f, 1.30f, 0.85f, 1.0f, 1.20f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 0, 0.0f, 0.0f, {255, 120, 0}}},
        // 기동형
        {"파일럿", {"파일럿", "파일럿", "기동형", "초월적 기동성으로 전장을 누빈다.", "대쉬 횟수", "이동속도 +30% · 대쉬 쿨타임 -35%", "데미지 -15%", 1.00f, 0.85f, 1.30f, 1.0f, 0.65f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 0, 0.0f, 0.0f, {100, 255, 180}}},
        {"광속", {"광속", "광속", "기동형", "빛보다 빠르게 움직인다. 회피가 곧 공격이다.", "대쉬 횟수", "이동속도 +55% · 대쉬 2연속", "HP -25% · 데미지 -20%", 0.75f, 0.80f, 1.55f, 1.0f, 0.50f, 1.0f, 1.0f, 1.0f, true, false, 1.0f, 0, 0.0f, 0.0f, {255, 230, 80}}},
        {"시공돌격자", {"시공돌격자", "시공돌격자", "기동형", "연속 대쉬와 긴 무적 시간을 갖는다.", "직업 상점 해금", "대쉬 쿨타임 -40% · 이동속도 +20% · 대쉬무적 +10프레임", "최대 HP -20% · 쉴드 -10%", 0.80f, 1.00f, 1.20f, 0.90f, 0.60f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 0, 0.0f, 0.0f, {0, 255, 255}}},
        // 마법형
        {"마법사", {"마법사", "마법사", "마법형", "스킬의 힘을 극한까지 끌어올린다.", "스킬 사용", "스킬 쿨타임 -40% · 스킬 데미지 +50%", "최대 HP -20%", 0.80f, 1.00f, 1.00f, 1.0f, 1.0f, 0.60f, 1.50f, 1.0f, false, false, 1.0f, 0, 0.0f, 0.0f, {180, 80, 255}}},
        {"차원술사", {"차원술사", "차원술사", "마법형", "차원의 경계를 자유로이 오간다.", "차원 전환", "공허 데미지 +70% · 차원 면역", "물질계 데미지 -10%", 1.00f, 0.90f, 1.00f, 1.10f, 1.0f, 1.0f, 1.0f, 1.70f, false, true, 1.0f, 0, 0.0f, 0.0f, {0, 200, 255}}},
        {"암흑학자", {"암흑학자", "암흑학자", "마법형", "어둠의 지배 아래 스킬을 쏟아낸다.", "직업 상점 해금", "스킬 쿨타임 -25% · 공허 데미지 +60%", "기본 무기 데미지 -20%", 1.00f, 0.80f, 1.00f, 1.0f, 1.0f, 0.75f, 1.0f, 1.60f, false, false, 1.0f, 0, 0.0f, 0.0f, {150, 0, 255}}},
        // 전술형
        {"흡혈귀", {"흡혈귀", "흡혈귀", "전술형", "적의 피를 마셔 상처를 치유한다.", "흡혈 처치", "처치 시 체력 회복 +3 · HP +25%", "쉴드 없음", 1.25f, 1.00f, 1.00f, 0.0f, 1.0f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 3, 0.0f, 0.0f, {180, 0, 80}}},
        {"연금술사", {"연금술사", "연금술사", "전술형", "획득 재화와 회복량을 증폭시킨다.", "직업 상점 해금", "골드/다이아몬드 획득 +35% · 포션 회복 +50%", "기본 데미지 -10%", 1.00f, 0.90f, 1.00f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 0, 0.35f, 0.50f, {80, 220, 120}}},
        {"사령관", {"사령관", "사령관", "전술형", "소환체의 화력을 극대화한다.", "직업 상점 해금", "소환수 공격력 +100% · 사격 속도 +30%", "본체 무기 발사 쿨타임 +30%", 1.00f, 1.00f, 1.00f, 1.0f, 1.30f, 1.0f, 1.0f, 1.0f, false, false, 1.0f, 0, 0.0f, 0.0f, {220, 220, 50}}}
    };
    return jobs;
}

