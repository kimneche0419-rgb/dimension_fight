cmake_minimum_required(VERSION 3.16)
project(DimensionFight LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# MSYS2 MinGW paths
set(MSYS2_ROOT "C:/msys64/mingw64")

# Source files
set(SOURCES
    src/main.cpp
)

# Headers (for IDE awareness)
set(HEADERS
    src/vec2.h
    src/utils.h
    src/data.h
    src/particles.h
    src/camera.h
    src/starfield.h
    src/projectile.h
    src/player.h
    src/enemy.h
    src/sound.h
    src/save.h
    src/ui.h
    src/game.h
)

add_executable(${PROJECT_NAME} ${SOURCES} ${HEADERS})

# Include paths
target_include_directories(${PROJECT_NAME} PRIVATE
    ${MSYS2_ROOT}/include
    ${MSYS2_ROOT}/include/SDL2
)

# Library paths
target_link_directories(${PROJECT_NAME} PRIVATE
    ${MSYS2_ROOT}/lib
)

# Link libraries
target_link_libraries(${PROJECT_NAME} PRIVATE
    mingw32
    SDL2main
    SDL2
    SDL2_image
    SDL2_mixer
    SDL2_ttf
    ws2_32
)

# Copy SDL2 DLLs to build directory after build
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${MSYS2_ROOT}/bin/SDL2.dll"
        "${MSYS2_ROOT}/bin/SDL2_image.dll"
        "${MSYS2_ROOT}/bin/SDL2_mixer.dll"
        "${MSYS2_ROOT}/bin/SDL2_ttf.dll"
        "${MSYS2_ROOT}/bin/libfreetype-6.dll"
        "${MSYS2_ROOT}/bin/zlib1.dll"
        "${MSYS2_ROOT}/bin/libpng16-16.dll"
        "${MSYS2_ROOT}/bin/libbz2-1.dll"
        "${MSYS2_ROOT}/bin/libbrotlidec.dll"
        "${MSYS2_ROOT}/bin/libbrotlicommon.dll"
        "${MSYS2_ROOT}/bin/libharfbuzz-0.dll"
        "${MSYS2_ROOT}/bin/libglib-2.0-0.dll"
        "${MSYS2_ROOT}/bin/libintl-8.dll"
        "${MSYS2_ROOT}/bin/libiconv-2.dll"
        "${MSYS2_ROOT}/bin/libgraphite2.dll"
        "${MSYS2_ROOT}/bin/libstdc++-6.dll"
        "${MSYS2_ROOT}/bin/libgcc_s_seh-1.dll"
        "${MSYS2_ROOT}/bin/libwinpthread-1.dll"
        $<TARGET_FILE_DIR:${PROJECT_NAME}>
    COMMENT "Copying SDL2 DLLs..."
)

# Copy assets directory
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CMAKE_SOURCE_DIR}/../assets"
        "$<TARGET_FILE_DIR:${PROJECT_NAME}>/assets"
    COMMENT "Copying game assets..."
)

# Windows subsystem (no console window in release)
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set_target_properties(${PROJECT_NAME} PROPERTIES
        WIN32_EXECUTABLE TRUE
    )
endif()
