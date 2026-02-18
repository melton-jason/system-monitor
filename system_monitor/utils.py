import re

MINUTE = 60

byte_units = {
    "B": 1,
    "KB": 10**3,
    "MB": 10**6,
    "GB": 10**9,
    "TB": 10**12,

    "KiB": 2**10,
    "MiB": 2**20,
    "GiB": 2**30,
    "TiB": 2**40,
}

def parse_byte_string(byte_string: str) -> int:
    formatted = re.sub(r"(\d+)\s*(\w+)", r"\1 \2", byte_string.strip()).split()
    if len(formatted) != 2:
        raise ValueError(f"Can not parse byte string: {byte_string}")
    number, unit = formatted

    return int(float(number) * byte_units[unit])