"""
Comfy Headless - Secrets (Compatibility Alias)
===============================================

This module re-exports everything from secrets_manager for backwards compatibility.
The canonical implementation lives in comfy_headless.secrets_manager.

Usage:
    from comfy_headless.secrets import SecretValue, get_secret
"""

from .secrets_manager import (
    DOTENV_AVAILABLE,
    VAULT_AVAILABLE,
    SecretsManager,
    SecretsManagerConfig,
    SecretValue,
    generate_api_key,
    generate_token,
    get_secret,
    get_secret_str,
    get_secrets_manager,
    hash_secret,
    mask_url_credentials,
    redact_dict,
    verify_hashed_secret,
)

__all__ = [
    "SecretValue",
    "SecretsManager",
    "SecretsManagerConfig",
    "get_secrets_manager",
    "get_secret",
    "get_secret_str",
    "generate_token",
    "generate_api_key",
    "hash_secret",
    "verify_hashed_secret",
    "mask_url_credentials",
    "redact_dict",
    "DOTENV_AVAILABLE",
    "VAULT_AVAILABLE",
]
