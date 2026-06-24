#pragma once
#include <string>
#include <fstream>
#include <vector>
#include <map>
#include <algorithm>
#include <cctype>

struct SaveData {
    int gold = 0;
    int diamonds = 0;
    int highScore = 0;
    int upgrades[6] = {0};  // shield, speed, hp, xp, dash, dmg

    // Resources
    int crystals = 0;
    int boss_cores = 0;
    int void_essences = 0;
    int abyss_pearls = 0;
    int time_shards = 0;

    // Gacha
    int gacha_tickets = 100;
    int gacha_pity_count = 0;

    // Active configurations
    std::string player_job = "";
    std::string equipped_fruit = "";

    // Collections
    std::vector<std::string> equipped_skills;
    std::vector<std::string> unlocked_jobs = {"전사", "저격수", "파일럿", "마법사", "흡혈귀", "기계공", "탱커", "광속", "차원술사", "학살자"};
    std::map<std::string, int> owned_skills;
    std::map<std::string, int> owned_anime_fruits;
    std::map<std::string, int> job_upgrades;
    std::map<std::string, int> crafted_items;
    std::map<std::string, int> fruit_awakenings;

    void save(const std::string& path = "save_data_cpp.json") {
        std::ofstream f(path);
        if (!f.is_open()) return;
        f << "{\n";
        f << "  \"gold\": " << gold << ",\n";
        f << "  \"diamonds\": " << diamonds << ",\n";
        f << "  \"crystals\": " << crystals << ",\n";
        f << "  \"boss_cores\": " << boss_cores << ",\n";
        f << "  \"void_essences\": " << void_essences << ",\n";
        f << "  \"abyss_pearls\": " << abyss_pearls << ",\n";
        f << "  \"time_shards\": " << time_shards << ",\n";
        f << "  \"high_score\": " << highScore << ",\n";
        f << "  \"gacha_tickets\": " << gacha_tickets << ",\n";
        f << "  \"gacha_pity_count\": " << gacha_pity_count << ",\n";
        f << "  \"player_job\": \"" << player_job << "\",\n";
        f << "  \"equipped_fruit\": \"" << equipped_fruit << "\",\n";
        f << "  \"shield_boost\": " << upgrades[0] << ",\n";
        f << "  \"speed_boost\": " << upgrades[1] << ",\n";
        f << "  \"hp_boost\": " << upgrades[2] << ",\n";
        f << "  \"xp_bonus\": " << upgrades[3] << ",\n";
        f << "  \"dash_cdr\": " << upgrades[4] << ",\n";
        f << "  \"dmg_boost\": " << upgrades[5] << ",\n";

        // Save maps
        f << "  \"owned_skills\": {";
        bool first = true;
        for (auto& [k, v] : owned_skills) {
            if (!first) f << ", ";
            f << "\"" << k << "\": " << v;
            first = false;
        }
        f << "},\n";

        f << "  \"owned_anime_fruits\": {";
        first = true;
        for (auto& [k, v] : owned_anime_fruits) {
            if (!first) f << ", ";
            f << "\"" << k << "\": " << v;
            first = false;
        }
        f << "},\n";

        f << "  \"job_upgrades\": {";
        first = true;
        for (auto& [k, v] : job_upgrades) {
            if (!first) f << ", ";
            f << "\"" << k << "\": " << v;
            first = false;
        }
        f << "},\n";

        f << "  \"crafted_items\": {";
        first = true;
        for (auto& [k, v] : crafted_items) {
            if (!first) f << ", ";
            f << "\"" << k << "\": " << v;
            first = false;
        }
        f << "},\n";

        f << "  \"fruit_awakenings\": {";
        first = true;
        for (auto& [k, v] : fruit_awakenings) {
            if (!first) f << ", ";
            f << "\"" << k << "\": " << v;
            first = false;
        }
        f << "},\n";

        // Save lists
        f << "  \"equipped_skills\": [";
        first = true;
        for (auto& s : equipped_skills) {
            if (!first) f << ", ";
            f << "\"" << s << "\"";
            first = false;
        }
        f << "],\n";

        f << "  \"unlocked_jobs\": [";
        first = true;
        for (auto& j : unlocked_jobs) {
            if (!first) f << ", ";
            f << "\"" << j << "\"";
            first = false;
        }
        f << "]\n";

        f << "}\n";
    }

    void load(const std::string& path = "save_data_cpp.json") {
        std::ifstream f(path);
        if (!f.is_open()) return;

        std::string line;
        while (std::getline(f, line)) {
            auto parseVal = [&](const std::string& key) -> int {
                auto pos = line.find("\"" + key + "\"");
                if (pos == std::string::npos) return -99999;
                auto colon = line.find(':', pos);
                if (colon == std::string::npos) return -99999;
                std::string numStr;
                for (size_t i = colon + 1; i < line.size(); i++) {
                    char c = line[i];
                    if (c == '-' || (c >= '0' && c <= '9')) numStr += c;
                    else if (!numStr.empty()) break;
                }
                return numStr.empty() ? 0 : std::stoi(numStr);
            };

            auto parseStr = [&](const std::string& key) -> std::string {
                auto pos = line.find("\"" + key + "\"");
                if (pos == std::string::npos) return "__not_found__";
                auto colon = line.find(':', pos);
                if (colon == std::string::npos) return "__not_found__";
                auto q1 = line.find('\"', colon);
                if (q1 == std::string::npos) return "__not_found__";
                auto q2 = line.find('\"', q1 + 1);
                if (q2 == std::string::npos) return "__not_found__";
                return line.substr(q1 + 1, q2 - q1 - 1);
            };

            auto parseMap = [&](const std::string& key) -> std::map<std::string, int> {
                std::map<std::string, int> res;
                auto pos = line.find("\"" + key + "\"");
                if (pos == std::string::npos) return res;
                auto braceOpen = line.find('{', pos);
                auto braceClose = line.find('}', pos);
                if (braceOpen == std::string::npos || braceClose == std::string::npos) return res;
                
                std::string content = line.substr(braceOpen + 1, braceClose - braceOpen - 1);
                size_t p = 0;
                while (true) {
                    auto q1 = content.find('\"', p);
                    if (q1 == std::string::npos) break;
                    auto q2 = content.find('\"', q1 + 1);
                    if (q2 == std::string::npos) break;
                    std::string k = content.substr(q1 + 1, q2 - q1 - 1);
                    
                    auto colon = content.find(':', q2 + 1);
                    if (colon == std::string::npos) break;
                    
                    std::string vStr;
                    size_t nextComma = content.find(',', colon + 1);
                    if (nextComma == std::string::npos) {
                        vStr = content.substr(colon + 1);
                    } else {
                        vStr = content.substr(colon + 1, nextComma - colon - 1);
                    }
                    vStr.erase(std::remove_if(vStr.begin(), vStr.end(), [](unsigned char c) { return std::isspace(c); }), vStr.end());
                    int val = vStr.empty() ? 0 : std::stoi(vStr);
                    res[k] = val;
                    
                    if (nextComma == std::string::npos) break;
                    p = nextComma + 1;
                }
                return res;
            };

            auto parseList = [&](const std::string& key) -> std::vector<std::string> {
                std::vector<std::string> res;
                auto pos = line.find("\"" + key + "\"");
                if (pos == std::string::npos) return res;
                auto bracketOpen = line.find('[', pos);
                auto bracketClose = line.find(']', pos);
                if (bracketOpen == std::string::npos || bracketClose == std::string::npos) return res;
                
                std::string content = line.substr(bracketOpen + 1, bracketClose - bracketOpen - 1);
                size_t p = 0;
                while (true) {
                    auto q1 = content.find('\"', p);
                    if (q1 == std::string::npos) break;
                    auto q2 = content.find('\"', q1 + 1);
                    if (q2 == std::string::npos) break;
                    std::string item = content.substr(q1 + 1, q2 - q1 - 1);
                    res.push_back(item);
                    
                    auto nextComma = content.find(',', q2 + 1);
                    if (nextComma == std::string::npos) break;
                    p = nextComma + 1;
                }
                return res;
            };

            int v;
            if ((v = parseVal("gold")) != -99999) gold = v;
            if ((v = parseVal("diamonds")) != -99999) diamonds = v;
            if ((v = parseVal("crystals")) != -99999) crystals = v;
            if ((v = parseVal("boss_cores")) != -99999) boss_cores = v;
            if ((v = parseVal("void_essences")) != -99999) void_essences = v;
            if ((v = parseVal("abyss_pearls")) != -99999) abyss_pearls = v;
            if ((v = parseVal("time_shards")) != -99999) time_shards = v;
            if ((v = parseVal("high_score")) != -99999) highScore = v;
            if ((v = parseVal("gacha_tickets")) != -99999) gacha_tickets = v;
            if ((v = parseVal("gacha_pity_count")) != -99999) gacha_pity_count = v;

            std::string s;
            if ((s = parseStr("player_job")) != "__not_found__") player_job = s;
            if ((s = parseStr("equipped_fruit")) != "__not_found__") equipped_fruit = s;

            if ((v = parseVal("shield_boost")) != -99999) upgrades[0] = v;
            if ((v = parseVal("speed_boost")) != -99999) upgrades[1] = v;
            if ((v = parseVal("hp_boost")) != -99999) upgrades[2] = v;
            if ((v = parseVal("xp_bonus")) != -99999) upgrades[3] = v;
            if ((v = parseVal("dash_cdr")) != -99999) upgrades[4] = v;
            if ((v = parseVal("dmg_boost")) != -99999) upgrades[5] = v;

            // Maps
            if (line.find("\"owned_skills\"") != std::string::npos) {
                owned_skills = parseMap("owned_skills");
            }
            if (line.find("\"owned_anime_fruits\"") != std::string::npos) {
                owned_anime_fruits = parseMap("owned_anime_fruits");
            }
            if (line.find("\"job_upgrades\"") != std::string::npos) {
                job_upgrades = parseMap("job_upgrades");
            }
            if (line.find("\"crafted_items\"") != std::string::npos) {
                crafted_items = parseMap("crafted_items");
            }
            if (line.find("\"fruit_awakenings\"") != std::string::npos) {
                fruit_awakenings = parseMap("fruit_awakenings");
            }

            // Lists
            if (line.find("\"equipped_skills\"") != std::string::npos) {
                equipped_skills = parseList("equipped_skills");
            }
            if (line.find("\"unlocked_jobs\"") != std::string::npos) {
                unlocked_jobs = parseList("unlocked_jobs");
            }
        }
    }
};
