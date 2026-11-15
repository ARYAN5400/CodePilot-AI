import re

import pytest
from cryptography.fernet import Fernet

from app.security import decrypt_token, digest_secret, encrypt_token, new_secret, pkce_pair


def test_random_state_is_url_safe_and_unique():
    first = new_secret()
    second = new_secret()
    assert first != second
    assert re.fullmatch(r"[A-Za-z0-9_-]+", first)


def test_pkce_pair_matches_s256_shape():
    verifier, challenge = pkce_pair()
    assert 43 <= len(verifier) <= 128
    assert len(challenge) == 43
    assert re.fullmatch(r"[A-Za-z0-9_-]+", challenge)
    assert verifier != challenge


def test_session_lookup_uses_one_way_digest():
    value = new_secret()
    digest = digest_secret(value)
    assert digest != value
    assert digest == digest_secret(value)
    assert len(digest) == 64


def test_encrypted_tokens_round_trip_and_are_not_plaintext():
    key = Fernet.generate_key().decode("ascii")
    token = "ghu_demo-token-never-log-me"
    ciphertext = encrypt_token(token, key)
    assert token not in ciphertext
    assert decrypt_token(ciphertext, key) == token


def test_wrong_encryption_key_does_not_decrypt():
    ciphertext = encrypt_token("sample", Fernet.generate_key().decode("ascii"))
    other_key = Fernet.generate_key().decode("ascii")
    with pytest.raises(Exception):
        decrypt_token(ciphertext, other_key)
