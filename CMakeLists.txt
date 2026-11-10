cmake_minimum_required(VERSION 3.18)
project(ra_hash_checker LANGUAGES C)
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
set(VENDOR "${CMAKE_CURRENT_SOURCE_DIR}/src/ra_hash_checker/_vendor/rcheevos")
if(EXISTS "${VENDOR}/src/hash/rc_hash.c")
    set(HASH_DIR "${VENDOR}/src/hash")
    set(UTIL_DIR "${VENDOR}/src/util")
    set(TEST_DIR "${VENDOR}/test/hash")
    set(HASH_PREFIX "rc_")
    set(TEST_DATA "hash_data.c")
    set(MD5_SOURCE "${UTIL_DIR}/md5.c")
else()
    set(HASH_DIR "${VENDOR}/src/rhash")
    set(UTIL_DIR "${VENDOR}/src")
    set(TEST_DIR "${VENDOR}/test/rhash")
    set(HASH_PREFIX "")
    set(TEST_DATA "data.c")
    set(MD5_SOURCE "${HASH_DIR}/md5.c")
endif()
set(HASH_SOURCES
    ${UTIL_DIR}/rc_compat.c
    ${HASH_DIR}/${HASH_PREFIX}hash.c
    ${HASH_DIR}/${HASH_PREFIX}hash_rom.c
    ${HASH_DIR}/${HASH_PREFIX}hash_disc.c
    ${HASH_DIR}/${HASH_PREFIX}cdreader.c
    ${MD5_SOURCE})
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
        ${TEST_DIR}/${TEST_DATA}
        ${TEST_DIR}/mock_filereader.c
        ${TEST_DIR}/test_${HASH_PREFIX}hash.c
        ${TEST_DIR}/test_${HASH_PREFIX}hash_rom.c
        ${TEST_DIR}/test_${HASH_PREFIX}hash_disc.c
        ${TEST_DIR}/test_${HASH_PREFIX}cdreader.c)
    target_include_directories(hash_vectors PRIVATE ${VENDOR}/include ${HASH_DIR} ${VENDOR}/test)
    target_compile_definitions(hash_vectors PRIVATE RC_STATIC RC_HASH_NO_ENCRYPTED RC_HASH_NO_ZIP)
    if(WIN32)
        target_compile_definitions(hash_vectors PRIVATE WINVER=0x0601 _WIN32_WINNT=0x0601 _CRT_SECURE_NO_WARNINGS)
    else()
        target_compile_definitions(hash_vectors PRIVATE _FILE_OFFSET_BITS=64 _LARGEFILE64_SOURCE)
    endif()
    add_test(NAME official_hash_vectors COMMAND hash_vectors)
endif()