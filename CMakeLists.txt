cmake_minimum_required(VERSION 3.18)
project(ra_hash_checker LANGUAGES C)
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
set(VENDOR "${CMAKE_CURRENT_SOURCE_DIR}/src/ra_hash_checker/_vendor/rcheevos")
set(HASH_SOURCES
    ${VENDOR}/src/rc_compat.c
    ${VENDOR}/src/rhash/hash.c
    ${VENDOR}/src/rhash/hash_rom.c
    ${VENDOR}/src/rhash/hash_disc.c
    ${VENDOR}/src/rhash/cdreader.c
    ${VENDOR}/src/rhash/md5.c)
Python_add_library(_rcheevos MODULE WITH_SOABI src/ra_hash_checker/native/bridge.c ${HASH_SOURCES})
target_include_directories(_rcheevos PRIVATE ${VENDOR}/include)
target_compile_definitions(_rcheevos PRIVATE RC_STATIC RC_HASH_NO_ENCRYPTED RC_HASH_NO_ZIP)
if(WIN32)
    target_compile_definitions(_rcheevos PRIVATE WINVER=0x0601 _WIN32_WINNT=0x0601)
else()
    target_compile_definitions(_rcheevos PRIVATE _FILE_OFFSET_BITS=64 _LARGEFILE64_SOURCE)
endif()
install(TARGETS _rcheevos LIBRARY DESTINATION ra_hash_checker RUNTIME DESTINATION ra_hash_checker)

option(RA_BUILD_TESTS "Build the pinned upstream synthetic hash tests" OFF)
if(RA_BUILD_TESTS)
    enable_testing()
    add_executable(hash_vectors tests/native_vectors.c ${HASH_SOURCES}
        ${VENDOR}/test/rhash/data.c
        ${VENDOR}/test/rhash/mock_filereader.c
        ${VENDOR}/test/rhash/test_hash.c
        ${VENDOR}/test/rhash/test_hash_rom.c
        ${VENDOR}/test/rhash/test_hash_disc.c
        ${VENDOR}/test/rhash/test_cdreader.c)
    target_include_directories(hash_vectors PRIVATE ${VENDOR}/include ${VENDOR}/src/rhash ${VENDOR}/test)
    target_compile_definitions(hash_vectors PRIVATE RC_STATIC RC_HASH_NO_ENCRYPTED RC_HASH_NO_ZIP)
    if(WIN32)
        target_compile_definitions(hash_vectors PRIVATE WINVER=0x0601 _WIN32_WINNT=0x0601 _CRT_SECURE_NO_WARNINGS)
    else()
        target_compile_definitions(hash_vectors PRIVATE _FILE_OFFSET_BITS=64 _LARGEFILE64_SOURCE)
    endif()
    add_test(NAME official_hash_vectors COMMAND hash_vectors)
endif()