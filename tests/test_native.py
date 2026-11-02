import hashlib
import struct

import pytest

from ra_hash_checker.native import HashError, calculate_hash


def ds_image() -> bytearray:
    image = bytearray(0x1000)
    struct.pack_into("<I", image, 0x20, 0x200)
    struct.pack_into("<I", image, 0x2C, 16)
    struct.pack_into("<I", image, 0x30, 0x300)
    struct.pack_into("<I", image, 0x3C, 8)
    struct.pack_into("<I", image, 0x68, 0x600)
    image[0x200:0x210] = b"ARM9 test data!!"
    image[0x300:0x308] = b"ARM7test"
    image[0x600:] = bytes(range(256)) * 10
    return image


def test_ds_reference_payload(tmp_path):
    image = ds_image()
    path = tmp_path / "Test ROM.nds"
    path.write_bytes(image)
    expected = hashlib.md5(image[:0x160] + image[0x200:0x210] + image[0x300:0x308] + image[0x600:]).hexdigest()
    assert calculate_hash(path, 18) == expected


def test_ds_short_icon_zero_padding(tmp_path):
    image = ds_image()[:0x610]
    path = tmp_path / "short.nds"
    path.write_bytes(image)
    payload = image[:0x160] + image[0x200:0x210] + image[0x300:0x308] + image[0x600:] + bytes(0x9F0)
    assert calculate_hash(path, 18) == hashlib.md5(payload).hexdigest()


def test_ds_invalid_header(tmp_path):
    path = tmp_path / "bad.nds"
    path.write_bytes(b"not a ROM")
    with pytest.raises(HashError):
        calculate_hash(path, 18)


@pytest.mark.parametrize("console_id,header", [
    (7, b"NES\x1a" + bytes(12)),
    (81, b"FDS\x1a" + bytes(12)),
    (13, b"LYNX\0" + bytes(59)),
    (51, b"\x01ATARI7800" + bytes(118)),
    (3, bytes(512)),
    (8, bytes(512)),
])
def test_header_normalization(tmp_path, console_id, header):
    payload = bytes(range(256)) * 512
    path = tmp_path / "header.rom"
    path.write_bytes(header + payload)
    assert calculate_hash(path, console_id) == hashlib.md5(payload).hexdigest()


def test_n64_byte_order(tmp_path):
    original = b"\x80\x37\x12\x40" + bytes(range(256)) * 256
    expected = hashlib.md5(original).hexdigest()
    for extension, stride in [("z64", 1), ("v64", 2), ("n64", 4)]:
        content = b"".join(original[offset:offset + stride][::-1] for offset in range(0, len(original), stride))
        path = tmp_path / f"game.{extension}"
        path.write_bytes(content)
        assert calculate_hash(path, 2) == expected


@pytest.mark.parametrize("extension", ["zip", "7z"])
def test_arcade_hashes_case_sensitive_filename(tmp_path, extension):
    for name in ["galaga", "GALAGA"]:
        path = tmp_path / f"{name}.{extension}"
        path.write_bytes(b"archive contents are not read")
        assert calculate_hash(path, 27) == hashlib.md5(name.encode()).hexdigest()


def test_arduboy_line_endings(tmp_path):
    path = tmp_path / "game.hex"
    content = b":1234567890\n:00000001FF\n"
    path.write_bytes(content.replace(b"\n", b"\r\n"))
    assert calculate_hash(path, 71) == hashlib.md5(content).hexdigest()


def test_unicode_path(tmp_path):
    path = tmp_path / "Pok\u00e9mon \u65e5\u672c.gb"
    path.write_bytes(b"synthetic ROM")
    assert calculate_hash(path, 4) == hashlib.md5(path.read_bytes()).hexdigest()