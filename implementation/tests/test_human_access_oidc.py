"""Cryptographic acceptance for the provider-neutral OIDC verifier."""

from __future__ import annotations

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from mvp_vertical import human_access


class _SigningKey:
    def __init__(self, key):
        self.key = key


class _StaticJwksClient:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, _token: str):
        return _SigningKey(self.key)


def _verifier(public_key) -> human_access.OidcJwtVerifier:
    verifier = human_access.OidcJwtVerifier(
        issuer="https://id.example.test/",
        audience="pantheon-cockpit",
        jwks_url="https://id.example.test/jwks/",
        algorithms=("RS256",),
    )
    verifier._jwks_client = _StaticJwksClient(public_key)
    return verifier


def _token(private_key, **overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": "https://id.example.test/",
        "sub": "human-42",
        "aud": "pantheon-cockpit",
        "iat": now,
        "exp": now + 300,
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256")


def test_oidc_verifier_accepts_valid_rs256_token() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = _verifier(private_key.public_key())
    claims = verifier.verify(_token(private_key))
    assert claims["sub"] == "human-42"
    assert claims["iss"] == "https://id.example.test/"


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://wrong.example.test/"},
        {"aud": "wrong-audience"},
        {"exp": 1},
        {"sub": ""},
    ],
)
def test_oidc_verifier_fails_closed_on_invalid_standard_claims(overrides) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = _verifier(private_key.public_key())
    with pytest.raises(human_access.AuthenticationFailed):
        verifier.verify(_token(private_key, **overrides))


def test_oidc_verifier_rejects_wrong_signature() -> None:
    trusted = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    attacker = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = _verifier(trusted.public_key())
    with pytest.raises(human_access.AuthenticationFailed):
        verifier.verify(_token(attacker))


def test_partial_oidc_environment_configuration_fails_instead_of_downgrading(monkeypatch) -> None:
    monkeypatch.setenv("MVP_OIDC_ISSUER", "https://id.example.test/")
    monkeypatch.delenv("MVP_OIDC_AUDIENCE", raising=False)
    monkeypatch.delenv("MVP_OIDC_JWKS_URL", raising=False)
    with pytest.raises(human_access.AccessConfigurationError):
        human_access.OidcJwtVerifier.from_env_optional()
