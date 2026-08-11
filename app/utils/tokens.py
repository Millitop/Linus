"""Card token and retrieval PIN generation.

Tokens are opaque random strings, looked up against the database -- there
is no offline/stateless verification requirement (the gate scanner always
talks to the local Flask app), so no HMAC signing is needed. See the plan
doc for the reasoning.
"""
import secrets
import string

_PIN_ALPHABET = string.digits


def generate_card_token(num_bytes: int = 32) -> str:
    return secrets.token_urlsafe(num_bytes)


def generate_retrieval_pin(length: int = 6) -> str:
    return "".join(secrets.choice(_PIN_ALPHABET) for _ in range(length))
