from pathlib import Path


class HashError(ValueError):
    pass


def calculate_hash(path: Path, console_id: int) -> str:
    from . import _rcheevos

    try:
        result = _rcheevos.generate(str(path.absolute()), console_id)
    except ValueError as error:
        raise HashError(str(error)) from None
    if len(result) != 32 or any(character not in "0123456789abcdef" for character in result):
        raise HashError("The hash engine did not return a valid MD5 hash.")
    return result