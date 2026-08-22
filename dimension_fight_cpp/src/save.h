#pragma once
#include <string>
#include <fstream>
#include <vector>
#include <map>
#include <algorithm>
#include <cctype>
#include <cstdio>

struct SaveData {
    int gold = 0;
    int diamonds = 0;
    int highScore = 0;
    int max_unlocked_chapter = 1;
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
    std::string username = "";
    std::string player_job = "";
    std::string equipped_fruit = "";
    std::string equipped_ship = "fighter";

    // Ship system
    std::map<std::string, int> ship_levels = {{"fighter", 1}};

    // Collections
    std::vector<std::string> equipped_skills;
    std::vector<std::string> unlocked_jobs = {"전사", "저격수", "파일럿", "마법사", "흡혈귀", "기계공", "탱커", "광속", "차원술사", "학살자"};
    std::map<std::string, int> owned_skills;
    std::map<std::string, int> owned_anime_fruits;
    std::map<std::string, int> job_upgrades;
    std::map<std::string, int> crafted_items;
    std::map<std::string, int> fruit_awakenings;

    // Escapes '"', '\\' and control characters so future user-supplied strings
    // (nicknames, guild names, etc.) can't corrupt the flat JSON save format.
    static std::string escapeJson(const std::string& s) {
        std::string out;
        out.reserve(s.size());
        for (unsigned char c : s) {
            switch (c) {
                case '\"': out += "\\\""; break;
                case '\\': out += "\\\\"; break;
                case '\n': out += "\\n"; break;
                case '\r': out += "\\r"; break;
                case '\t': out += "\\t"; break;
                default:
                    if (c < 0x20) {
                        char buf[8];
                        snprintf(buf, sizeof(buf), "\\u%04x", c);
                        out += buf;
                    } else {
                        out += (char)c;
                    }
            }
        }
        return out;
    }

    void save(const std::string& path = "save_data_cpp.json") {
        std::string tmpPath = path + ".tmp";
        std::ofstream f(tmpPath);
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
        f << "  \"username\": \"" << escapeJson(username) << "\",\n";
        f << "  \"player_job\": \"" << escapeJson(player_job) << "\",\n";
        f << "  \"equipped_fruit\": \"" << escapeJson(equipped_fruit) << "\",\n";
        f << "  \"equipped_ship\": \"" << escapeJson(equipped_ship) << "\",\n";
        f << "  \"shield_boost\": " << upgrades[0] << ",\n";
        f << "  \"speed_boost\": " << upgrades[1] << ",\n";
        f << "  \"hp_boost\": " << upgrades[2] << ",\n";
        f << "  \"xp_bonus\": " << upgrades[3] << ",\n";
        f << "  \"dash_cdr\": " << upgrades[4] << ",\n";
        f << "  \"dmg_boost\": " << upgrades[5] << ",\n";
        f << "  \"max_unlocked_chapter\": " << max_unlocked_chapter << ",\n";

        // Save maps
        f << "  \"owned_skills\": {";
        bool first = true;
        for (auto& [k, v] : owned_skills) {
            if (!first) f << ", ";
            f << "\"" << escapeJson(k) << "\": " << v;
            first = false;
        }
        f << "},\n";

        f << "  \"owned_anime_fruits\": {";
        first = true;
        for (auto& [k, v] : owned_anime_fruits) {
            if (!first) f << ", ";
            f << "\"" << escapeJson(k) << "\": " << v;
            first = false;
        }
        f << "},\n";

        f << "  \"job_upgrades\": {";
        first = true;
        for (auto& [k, v] : job_upgrades) {
            if (!first) f << ", ";
            f << "\"" << escapeJson(k) << "\": " << v;
            first = false;
        }
        f << "},\n";

        f << "  \"crafted_items\": {";
        first = true;
        for (auto& [k, v] : crafted_items) {
            if (!first) f << ", ";
            f << "\"" << escapeJson(k) << "\": " << v;
            first = false;
        }
        f << "},\n";

        f << "  \"fruit_awakenings\": {";
        first = true;
        for (auto& [k, v] : fruit_awakenings) {
            if (!first) f << ", ";
            f << "\"" << escapeJson(k) << "\": " << v;
            first = false;
        }
        f << "},\n";

        f << "  \"ship_levels\": {";
        first = true;
        for (auto& [k, v] : ship_levels) {
            if (!first) f << ", ";
            f << "\"" << escapeJson(k) << "\": " << v;
            first = false;
        }
        f << "},\n";

        // Save lists
        f << "  \"equipped_skills\": [";
        first = true;
        for (auto& s : equipped_skills) {
            if (!first) f << ", ";
            f << "\"" << escapeJson(s) << "\"";
            first = false;
        }
        f << "],\n";

        f << "  \"unlocked_jobs\": [";
        first = true;
        for (auto& j : unlocked_jobs) {
            if (!first) f << ", ";
            f << "\"" << escapeJson(j) << "\"";
            first = false;
        }
        f << "]\n";

        f << "}\n";
        f.close();

        // Keep a rolling backup of the last known-good save before replacing it.
        std::ifstream existsCheck(path);
        if (existsCheck.good()) {
            existsCheck.close();
            std::remove((path + ".bak").c_str());
            std::rename(path.c_str(), (path + ".bak").c_str());
        }

        // Atomically replace the save file so a crash/power-loss mid-write can
        // never leave a truncated, corrupt save_data_cpp.json behind.
        std::remove(path.c_str());
        std::rename(tmpPath.c_str(), path.c_str());
    }

    void load(const std::string& path = "save_data_cpp.json") {
        std::ifstream f(path);
        if (!f.is_open()) return;

        // Finds the unescaped closing quote starting search at `from` (a '\\' always
        // escapes the next character, so an escaped '\"' doesn't end the string early).
        auto findClosingQuote = [](const std::string& s, size_t from) -> size_t {
            size_t i = from;
            while (i < s.size()) {
                if (s[i] == '\\') { i += 2; continue; }
                if (s[i] == '\"') return i;
                i++;
            }
            return std::string::npos;
        };

        auto unescapeJson = [](const std::string& s) -> std::string {
            std::string out;
            out.reserve(s.size());
            for (size_t i = 0; i < s.size(); i++) {
                if (s[i] == '\\' && i + 1 < s.size()) {
                    char n = s[i + 1];
                    switch (n) {
                        case '\"': out += '\"'; i++; break;
                        case '\\': out += '\\'; i++; break;
                        case 'n': out += '\n'; i++; break;
                        case 'r': out += '\r'; i++; break;
                        case 't': out += '\t'; i++; break;
                        case 'u':
                            if (i + 5 < s.size()) {
                                try {
                                    int code = std::stoi(s.substr(i + 2, 4), nullptr, 16);
                                    out += (char)code;
                                } catch (...) {}
                                i += 5;
                            }
                            break;
                        default: out += n; i++; break;
                    }
                } else {
                    out += s[i];
                }
            }
            return out;
        };

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
                if (numStr.empty()) return 0;
                try { return std::stoi(numStr); } catch (...) { return 0; }
            };

            auto parseStr = [&](const std::string& key) -> std::string {
                auto pos = line.find("\"" + key + "\"");
                if (pos == std::string::npos) return "__not_found__";
                auto colon = line.find(':', pos);
                if (colon == std::string::npos) return "__not_found__";
                auto q1 = line.find('\"', colon);
                if (q1 == std::string::npos) return "__not_found__";
                auto q2 = findClosingQuote(line, q1 + 1);
                if (q2 == std::string::npos) return "__not_found__";
                return unescapeJson(line.substr(q1 + 1, q2 - q1 - 1));
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
                    auto q2 = findClosingQuote(content, q1 + 1);
                    if (q2 == std::string::npos) break;
                    std::string k = unescapeJson(content.substr(q1 + 1, q2 - q1 - 1));
                    
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
                    int val = 0;
                    if (!vStr.empty()) {
                        try { val = std::stoi(vStr); } catch (...) { val = 0; }
                    }
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
                    auto q2 = findClosingQuote(content, q1 + 1);
                    if (q2 == std::string::npos) break;
                    std::string item = unescapeJson(content.substr(q1 + 1, q2 - q1 - 1));
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
            if ((s = parseStr("username")) != "__not_found__") username = s;
            if ((s = parseStr("player_job")) != "__not_found__") player_job = s;
            if ((s = parseStr("equipped_fruit")) != "__not_found__") equipped_fruit = s;
            if ((s = parseStr("equipped_ship")) != "__not_found__") equipped_ship = s;

            if ((v = parseVal("shield_boost")) != -99999) upgrades[0] = v;
            if ((v = parseVal("speed_boost")) != -99999) upgrades[1] = v;
            if ((v = parseVal("hp_boost")) != -99999) upgrades[2] = v;
            if ((v = parseVal("xp_bonus")) != -99999) upgrades[3] = v;
            if ((v = parseVal("dash_cdr")) != -99999) upgrades[4] = v;
            if ((v = parseVal("dmg_boost")) != -99999) upgrades[5] = v;
            if ((v = parseVal("max_unlocked_chapter")) != -99999) max_unlocked_chapter = v;

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
            if (line.find("\"ship_levels\"") != std::string::npos) {
                ship_levels = parseMap("ship_levels");
                if (ship_levels.find("fighter") == ship_levels.end())
                    ship_levels["fighter"] = 1;
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
