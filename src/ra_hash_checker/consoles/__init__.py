from . import (
    amstrad_cpc, apple_ii, arcade, arduboy, atari_2600, atari_7800,
    atari_jaguar, atari_jaguar_cd, atari_lynx, channel_f, colecovision,
    dreamcast, famicom_disk_system, game_boy, game_boy_advance,
    game_boy_color, game_gear, gamecube, intellivision, master_system,
    mega_drive, mega_duck, msx, neo_geo_cd, neo_geo_pocket,
    neo_geo_pocket_color, nes, nintendo_64, nintendo_ds, odyssey2,
    pc_8800, pc_engine, pc_engine_cd, pc_fx, playstation, playstation_2,
    pokemon_mini, psp, saturn, sega_32x, sega_cd, sg_1000, snes,
    supervision, three_do, vectrex, virtual_boy, wasm4, wonderswan,
    wonderswan_color,
)

CONSOLES = tuple(module.CONSOLE for module in (
    three_do, amstrad_cpc, apple_ii, arcade, arduboy, atari_2600,
    atari_7800, atari_jaguar, atari_jaguar_cd, atari_lynx, wonderswan,
    wonderswan_color, colecovision, channel_f, vectrex, odyssey2,
    intellivision, msx, pc_8800, pc_engine, pc_engine_cd, pc_fx,
    famicom_disk_system, game_boy, game_boy_advance, game_boy_color,
    gamecube, nintendo_64, nintendo_ds, nes, pokemon_mini, snes,
    virtual_boy, neo_geo_cd, neo_geo_pocket, neo_geo_pocket_color,
    sega_32x, dreamcast, game_gear, master_system, mega_drive, sg_1000,
    saturn, sega_cd, playstation, playstation_2, psp, wasm4, supervision,
    mega_duck,
))