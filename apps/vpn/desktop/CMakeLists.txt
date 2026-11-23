cmake_minimum_required(VERSION 3.20)
project(WexumVPNDesktop LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(wexum_desktop_core STATIC src/connection.cpp src/locale.cpp)
target_include_directories(wexum_desktop_core PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/include")
if(MSVC)
  target_compile_options(wexum_desktop_core PRIVATE /W4 /WX)
else()
  target_compile_options(wexum_desktop_core PRIVATE -Wall -Wextra -Wpedantic -Werror)
endif()

include(CTest)
if(BUILD_TESTING)
  add_executable(wexum_desktop_tests tests/test_main.cpp)
  target_link_libraries(wexum_desktop_tests PRIVATE wexum_desktop_core)
  add_test(NAME wexum_desktop_core_tests COMMAND wexum_desktop_tests)
endif()

# The GUI is opt-in until Qt6 dependencies and platform runners are approved.
option(WEXUM_DESKTOP_BUILD_UI "Build the non-connecting Qt6 desktop shell" OFF)
if(WEXUM_DESKTOP_BUILD_UI)
  find_package(Qt6 6.5 REQUIRED COMPONENTS Widgets)
  add_executable(wexumvpn_desktop src/main.cpp)
  target_link_libraries(wexumvpn_desktop PRIVATE wexum_desktop_core Qt6::Widgets)
endif()
