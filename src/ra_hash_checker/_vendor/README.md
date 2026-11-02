# Vendored rcheevos

Source: https://github.com/RetroAchievements/rcheevos

Pinned commit: `1433173220a7eaede6a9ed7a18e94117be1821e0`.

The upstream license is preserved unchanged in `rcheevos/LICENSE`.
Upstream headers, hash sources and the selected synthetic hash tests are unchanged.
Only `rc_compat.c`, `hash.c`, `hash_rom.c`, `hash_disc.c`, `cdreader.c` and `md5.c`
are compiled. ROM and DISC are enabled; encrypted-content and ZIP-content hashing
are disabled. Arcade ZIP/7z filename hashing does not require ZIP-content support.
There is no runtime download and no Python reimplementation of upstream structs.

The small Python C bridge lives in `../native/bridge.c`. The optional CMake
`RA_BUILD_TESTS` target runs the upstream ROM, DISC, general hash and sector-reader
test suites with synthetic data, not commercial ROMs.