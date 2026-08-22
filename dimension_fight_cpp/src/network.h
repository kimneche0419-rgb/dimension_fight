#pragma once
#include <winsock2.h>
#include <ws2tcpip.h>
#include <string>
#include <vector>
#include <map>
#include <iostream>
#include <sstream>
#include <fstream>
#include <algorithm>
#include "save.h"

class NetworkClient {
public:
    SOCKET authSock = INVALID_SOCKET;
    SOCKET serverSock = INVALID_SOCKET; // Matchmaking socket
    SOCKET peerSock = INVALID_SOCKET;   // Gameplay relay socket
    bool wsaActive = false;
    bool loggedIn = false;
    std::string loggedUser = "";
    std::string currentSessionId = "";
    // Signed token issued by railway-auth on LOGIN; presented to match/relay so
    // they can verify the caller actually owns this username (prevents session
    // hijacking by anyone who just guesses a username or session id).
    std::string sessionToken = "";

    // Minimal single-line JSON string-field extractor (mirrors save.h's parseStr),
    // used to pull protocol fields like "session_token" out of the raw LOGIN_OK body.
    static std::string extractJsonStringField(const std::string& json, const std::string& key) {
        auto pos = json.find("\"" + key + "\"");
        if (pos == std::string::npos) return "";
        auto colon = json.find(':', pos);
        if (colon == std::string::npos) return "";
        auto q1 = json.find('\"', colon);
        if (q1 == std::string::npos) return "";
        auto q2 = json.find('\"', q1 + 1);
        if (q2 == std::string::npos) return "";
        return json.substr(q1 + 1, q2 - q1 - 1);
    }

    // Strips a "key": "value" pair (and its adjoining comma) out of a flat
    // single-line JSON blob, so the short-lived session token never ends up
    // written to disk in save_data_cpp.json.
    static std::string stripJsonStringField(const std::string& json, const std::string& key) {
        auto pos = json.find("\"" + key + "\"");
        if (pos == std::string::npos) return json;
        auto colon = json.find(':', pos);
        if (colon == std::string::npos) return json;
        auto q1 = json.find('\"', colon);
        if (q1 == std::string::npos) return json;
        auto q2 = json.find('\"', q1 + 1);
        if (q2 == std::string::npos) return json;
        size_t end = q2 + 1;
        if (end < json.size() && json[end] == ',') end++;
        std::string result = json.substr(0, pos) + json.substr(end);
        return result;
    }

    // Persists the short-lived signed session token (not the password) so
    // auto-login on next launch can't leak a reusable plaintext credential
    // from a file on disk. The token expires server-side (see railway-auth).
    void saveSession(const std::string& user, const std::string& token) {
        std::ofstream f("login_session.txt");
        if (f.is_open()) {
            f << user << "\n" << token << "\n";
            f.close();
        }
    }

    bool loadSession(std::string& outUser, std::string& outToken) {
        std::ifstream f("login_session.txt");
        if (!f.is_open()) return false;
        std::string u, t;
        if (std::getline(f, u) && std::getline(f, t)) {
            outUser = u;
            outToken = t;
            f.close();
            return true;
        }
        f.close();
        return false;
    }

    void clearSession() {
        std::remove("login_session.txt");
    }

    // Configurable host/port
    std::string authHost = "127.0.0.1";
    int authPort = 9000;
    std::string matchHost = "127.0.0.1";
    int matchPort = 9001;
    std::string relayHostFallback = "127.0.0.1";
    int relayPortFallback = 9002;

    NetworkClient() {
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) == 0) {
            wsaActive = true;
        } else {
            std::cerr << "WSAStartup failed\n";
        }
        loadConfig("server_config.txt");
    }

    ~NetworkClient() {
        cleanup();
        if (wsaActive) {
            WSACleanup();
        }
    }

    void loadConfig(const std::string& path) {
        std::ifstream f(path);
        if (!f.is_open()) {
            std::cout << "[Config] Failed to open " << path << ", using default local configuration.\n";
            return;
        }
        std::string line;
        while (std::getline(f, line)) {
            // Remove spaces and newlines
            line.erase(std::remove(line.begin(), line.end(), ' '), line.end());
            line.erase(std::remove(line.begin(), line.end(), '\r'), line.end());
            line.erase(std::remove(line.begin(), line.end(), '\n'), line.end());
            if (line.empty() || line[0] == '#') continue;

            size_t eq = line.find('=');
            if (eq == std::string::npos) continue;

            std::string key = line.substr(0, eq);
            std::string val = line.substr(eq + 1);

            auto parsePort = [](const std::string& s, int fallback) -> int {
                try { return std::stoi(s); } catch (...) { return fallback; }
            };

            if (key == "AUTH_HOST") authHost = val;
            else if (key == "AUTH_PORT") authPort = parsePort(val, authPort);
            else if (key == "MATCH_HOST") matchHost = val;
            else if (key == "MATCH_PORT") matchPort = parsePort(val, matchPort);
            else if (key == "RELAY_HOST") relayHostFallback = val;
            else if (key == "RELAY_PORT") relayPortFallback = parsePort(val, relayPortFallback);
        }
        f.close();
        std::cout << "[Config] Loaded server configuration:\n";
        std::cout << "  Auth: " << authHost << ":" << authPort << "\n";
        std::cout << "  Match: " << matchHost << ":" << matchPort << "\n";
    }

    void cleanup() {
        if (serverSock != INVALID_SOCKET) {
            closesocket(serverSock);
            serverSock = INVALID_SOCKET;
        }
        if (peerSock != INVALID_SOCKET) {
            closesocket(peerSock);
            peerSock = INVALID_SOCKET;
        }
        if (authSock != INVALID_SOCKET) {
            closesocket(authSock);
            authSock = INVALID_SOCKET;
        }
    }

    // connectTimeoutMs bounds how long a connect() attempt can block the caller
    // (previously relied on the OS default of ~21s on Windows, freezing the UI).
    bool connectToHost(const std::string& host, int port, SOCKET& outSock, int connectTimeoutMs = 5000) {
        if (outSock != INVALID_SOCKET) return true;
        outSock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (outSock == INVALID_SOCKET) return false;

        struct addrinfo hints, *result = nullptr;
        ZeroMemory(&hints, sizeof(hints));
        hints.ai_family = AF_INET;
        hints.ai_socktype = SOCK_STREAM;
        hints.ai_protocol = IPPROTO_TCP;

        std::string portStr = std::to_string(port);
        int r = getaddrinfo(host.c_str(), portStr.c_str(), &hints, &result);
        if (r != 0) {
            closesocket(outSock);
            outSock = INVALID_SOCKET;
            return false;
        }

        // Non-blocking connect + select() so an unreachable/firewalled host
        // fails fast instead of blocking the caller for the OS default timeout.
        u_long nbMode = 1;
        ioctlsocket(outSock, FIONBIO, &nbMode);

        int cr = connect(outSock, result->ai_addr, (int)result->ai_addrlen);
        bool connected = false;
        if (cr == 0) {
            connected = true;
        } else if (WSAGetLastError() == WSAEWOULDBLOCK) {
            fd_set writeSet, errSet;
            FD_ZERO(&writeSet);
            FD_ZERO(&errSet);
            FD_SET(outSock, &writeSet);
            FD_SET(outSock, &errSet);
            timeval tv;
            tv.tv_sec = connectTimeoutMs / 1000;
            tv.tv_usec = (connectTimeoutMs % 1000) * 1000;
            int sr = select(0, nullptr, &writeSet, &errSet, &tv);
            if (sr > 0 && FD_ISSET(outSock, &writeSet)) {
                int soErr = 0;
                int soErrLen = sizeof(soErr);
                if (getsockopt(outSock, SOL_SOCKET, SO_ERROR, (char*)&soErr, &soErrLen) == 0 && soErr == 0) {
                    connected = true;
                }
            }
        }

        freeaddrinfo(result);

        if (!connected) {
            closesocket(outSock);
            outSock = INVALID_SOCKET;
            return false;
        }

        // Switch to blocking mode with explicit send/recv timeouts so later
        // recv() calls can't hang forever if the server stalls or drops silently.
        u_long bMode = 0;
        ioctlsocket(outSock, FIONBIO, &bMode);
        DWORD sockTimeoutMs = 8000;
        setsockopt(outSock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&sockTimeoutMs, sizeof(sockTimeoutMs));
        setsockopt(outSock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&sockTimeoutMs, sizeof(sockTimeoutMs));

        return true;
    }

    // Helper to send line to socket
    bool sendLine(SOCKET s, const std::string& line) {
        std::string packet = line + "\n";
        int sent = send(s, packet.c_str(), (int)packet.size(), 0);
        return sent != SOCKET_ERROR;
    }

    // Helper to read line (with blocking/non-blocking support)
    std::string recvLine(SOCKET s, bool blocking = false) {
        std::string line = "";
        char c;
        while (true) {
            int r = recv(s, &c, 1, 0);
            if (r == 1) {
                if (c == '\n') break;
                line += c;
            } else if (r == SOCKET_ERROR) {
                int err = WSAGetLastError();
                if (err == WSAEWOULDBLOCK) {
                    if (blocking) {
                        Sleep(5);
                        continue;
                    }
                    return "__WOULD_BLOCK__";
                }
                return "__ERROR__";
            } else {
                return "__CLOSED__";
            }
        }
        return line;
    }

    bool registerUser(const std::string& user, const std::string& pass, const std::string& ip = "") {
        SOCKET s = INVALID_SOCKET;
        if (!connectToHost(authHost, authPort, s)) return false;
        
        // Temporarily set blocking
        u_long mode = 0; ioctlsocket(s, FIONBIO, &mode);
        bool ok = sendLine(s, "REGISTER " + user + " " + pass);
        if (!ok) {
            closesocket(s);
            return false;
        }
        std::string resp = recvLine(s, true);
        closesocket(s);

        return resp == "REGISTER_OK";
    }

    bool loginUser(const std::string& user, const std::string& pass, SaveData& outData, const std::string& ip = "") {
        if (authSock != INVALID_SOCKET) {
            closesocket(authSock);
            authSock = INVALID_SOCKET;
        }
        if (!connectToHost(authHost, authPort, authSock)) return false;

        u_long mode = 0; ioctlsocket(authSock, FIONBIO, &mode);
        bool ok = sendLine(authSock, "LOGIN " + user + " " + pass);
        if (!ok) {
            closesocket(authSock);
            authSock = INVALID_SOCKET;
            return false;
        }
        std::string resp = recvLine(authSock, true);
        
        // Set back to non-blocking
        mode = 1; ioctlsocket(authSock, FIONBIO, &mode);

        if (resp.rfind("LOGIN_OK", 0) == 0) {
            loggedIn = true;
            loggedUser = user;
            std::string jsonStr = resp.substr(9);
            sessionToken = extractJsonStringField(jsonStr, "session_token");
            saveSession(user, sessionToken);
            std::ofstream f("save_data_cpp.json");
            if (f.is_open()) {
                f << stripJsonStringField(jsonStr, "session_token");
                f.close();
            }
            outData.load();
            return true;
        }
        closesocket(authSock);
        authSock = INVALID_SOCKET;
        return false;
    }

    // Passwordless re-login used for the "remember me" auto-login on startup,
    // using the token saved by saveSession() instead of a stored password.
    bool loginWithToken(const std::string& user, const std::string& token, SaveData& outData) {
        if (authSock != INVALID_SOCKET) {
            closesocket(authSock);
            authSock = INVALID_SOCKET;
        }
        if (!connectToHost(authHost, authPort, authSock)) return false;

        u_long mode = 0; ioctlsocket(authSock, FIONBIO, &mode);
        bool ok = sendLine(authSock, "LOGIN_TOKEN " + user + " " + token);
        if (!ok) {
            closesocket(authSock);
            authSock = INVALID_SOCKET;
            return false;
        }
        std::string resp = recvLine(authSock, true);

        mode = 1; ioctlsocket(authSock, FIONBIO, &mode);

        if (resp.rfind("LOGIN_OK", 0) == 0) {
            loggedIn = true;
            loggedUser = user;
            std::string jsonStr = resp.substr(9);
            sessionToken = extractJsonStringField(jsonStr, "session_token");
            saveSession(user, sessionToken);
            std::ofstream f("save_data_cpp.json");
            if (f.is_open()) {
                f << stripJsonStringField(jsonStr, "session_token");
                f.close();
            }
            outData.load();
            return true;
        }
        closesocket(authSock);
        authSock = INVALID_SOCKET;
        clearSession(); // Stale/expired token — drop it so we stop retrying with it.
        return false;
    }

    bool saveUser(SaveData& data, const std::string& ip = "") {
        if (!loggedIn || authSock == INVALID_SOCKET) return false;
        data.save();
        std::ifstream f("save_data_cpp.json");
        if (!f.is_open()) return false;
        std::stringstream ss;
        ss << f.rdbuf();
        f.close();
        std::string jsonStr = ss.str();
        
        jsonStr.erase(std::remove(jsonStr.begin(), jsonStr.end(), '\n'), jsonStr.end());
        jsonStr.erase(std::remove(jsonStr.begin(), jsonStr.end(), '\r'), jsonStr.end());

        u_long mode = 0; ioctlsocket(authSock, FIONBIO, &mode);
        bool ok = sendLine(authSock, "SAVE " + jsonStr);
        if (!ok) {
            mode = 1; ioctlsocket(authSock, FIONBIO, &mode);
            return false;
        }
        std::string resp = recvLine(authSock, true);
        mode = 1; ioctlsocket(authSock, FIONBIO, &mode);

        return resp == "SAVE_OK";
    }

    bool startMatchmaking(const std::string& mode, const std::string& ip = "") {
        if (!loggedIn) return false;
        if (serverSock != INVALID_SOCKET) {
            closesocket(serverSock);
            serverSock = INVALID_SOCKET;
        }
        if (!connectToHost(matchHost, matchPort, serverSock)) return false;

        u_long m = 0; ioctlsocket(serverSock, FIONBIO, &m);
        sendLine(serverSock, "MATCH " + loggedUser + " " + sessionToken + " " + mode);
        std::string resp = recvLine(serverSock, true);
        m = 1; ioctlsocket(serverSock, FIONBIO, &m);
        return resp == "MATCH_QUEUED";
    }

    bool cancelMatchmaking(const std::string& ip = "") {
        if (serverSock == INVALID_SOCKET) return true;
        u_long m = 0; ioctlsocket(serverSock, FIONBIO, &m);
        sendLine(serverSock, "CANCEL " + loggedUser);
        std::string resp = recvLine(serverSock, true);
        closesocket(serverSock);
        serverSock = INVALID_SOCKET;
        return resp == "CANCEL_OK";
    }

    bool pollMatchResult(std::string& outRole, std::string& outIp, int& outPort, std::string& outPeer) {
        if (serverSock == INVALID_SOCKET) return false;
        std::string resp = recvLine(serverSock, false);
        if (resp == "__WOULD_BLOCK__" || resp == "__ERROR__" || resp == "__CLOSED__") {
            return false;
        }

        if (resp.rfind("MATCHED", 0) == 0) {
            std::stringstream ss(resp);
            std::string cmd, role, relayHost, relayPortStr, sessionId, peer;
            ss >> cmd >> role >> relayHost >> relayPortStr >> sessionId >> peer;
            
            outRole = role;
            outIp = relayHost;
            try { outPort = std::stoi(relayPortStr); } catch (...) { return false; }
            currentSessionId = sessionId;
            outPeer = peer;
            
            // We matched! Close matchmaking socket
            closesocket(serverSock);
            serverSock = INVALID_SOCKET;
            return true;
        }
        return false;
    }

    bool relayConnect(const std::string& host, int port, const std::string& sessionId, const std::string& role, const std::string& username) {
        if (peerSock != INVALID_SOCKET) {
            closesocket(peerSock);
            peerSock = INVALID_SOCKET;
        }
        if (!connectToHost(host, port, peerSock)) return false;

        // Temporarily set blocking for the INIT handshake
        u_long mode = 0; ioctlsocket(peerSock, FIONBIO, &mode);
        std::string initCmd = "INIT " + sessionId + " " + role + " " + username + " " + sessionToken;
        if (!sendLine(peerSock, initCmd)) {
            closesocket(peerSock);
            peerSock = INVALID_SOCKET;
            return false;
        }

        // Set non-blocking for gameplay loop
        mode = 1; ioctlsocket(peerSock, FIONBIO, &mode);
        std::cout << "[Relay] Connected to relay server at " << host << ":" << port << " for session " << sessionId << "\n";
        return true;
    }

    // Keep dummy p2pHost and p2pConnect just in case, returning false
    bool p2pHost(int port) { return false; }
    bool p2pConnect(const std::string& ip, int port) { return false; }
};
