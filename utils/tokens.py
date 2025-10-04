from string import ascii_letters, digits
import random

AVAILABLE_CHARS = ascii_letters + digits


def generate_random_tokens(length: int) -> str:
    return "".join(random.choices(AVAILABLE_CHARS, k=length))
