cmake_minimum_required(VERSION 3.20)
project(STATghost-NPP VERSION 0.1.0 LANGUAGES CXX RC)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(NPP_SDK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/vendor/npp-sdk")
set(NPP_DOCK_DIR "${NPP_SDK_DIR}/DockingFeature")

add_library(STATghost SHARED
    src/NppPluginExports.cpp
    src/PluginDefinition.cpp
    src/StatghostBridge.cpp
    src/StatghostChrome.cpp
    src/StatghostCommands.cpp
    src/StatghostConfigDlg.cpp
    src/StatghostHost.cpp
    src/StatghostIcons.cpp
    src/StatghostPanelDlg.cpp
    src/StatghostPrefs.cpp
    src/StatghostProtocol.cpp
    src/StatghostStatement.cpp
    src/StatghostTheme.cpp
    ${NPP_DOCK_DIR}/StaticDialog.cpp
    res/STATghost.rc
)

target_include_directories(STATghost PRIVATE
    src
    res
    ${NPP_SDK_DIR}
    ${NPP_DOCK_DIR}
)

target_compile_definitions(STATghost PRIVATE UNICODE _UNICODE WIN32_LEAN_AND_MEAN)
target_link_libraries(STATghost PRIVATE shlwapi gdiplus comdlg32 shell32)

if (MINGW)
    set_target_properties(STATghost PROPERTIES PREFIX "")
endif()

set_target_properties(STATghost PROPERTIES
    OUTPUT_NAME "STATghost"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin/STATghost"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin/STATghost"
    ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
)

add_executable(statghost_statement_test test/statement_test.cpp src/StatghostStatement.cpp)
target_include_directories(statghost_statement_test PRIVATE src)
target_compile_definitions(statghost_statement_test PRIVATE WIN32_LEAN_AND_MEAN)
