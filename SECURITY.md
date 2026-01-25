# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.5.x   | :white_check_mark: |
| < 2.5   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues by:
- **GitHub**: [Create a private security advisory](https://github.com/mcp-tool-shop/comfy-headless/security/advisories/new)

### What to Include

When reporting a vulnerability, please include:

1. **Description** - Clear description of the vulnerability
2. **Impact** - What could an attacker achieve?
3. **Reproduction steps** - How to reproduce the issue
4. **Affected versions** - Which versions are impacted
5. **Suggested fix** - If you have one (optional)

### What to Expect

1. **Acknowledgment** - We'll acknowledge receipt within 48 hours
2. **Assessment** - We'll assess severity and impact within 7 days
3. **Fix timeline** - Critical issues: 7 days, High: 14 days, Medium: 30 days
4. **Disclosure** - We'll coordinate disclosure timing with you
5. **Credit** - We'll credit you in the security advisory (unless you prefer anonymity)

## Security Defaults

comfy-headless is designed with secure defaults:

### UI Server Binding

```
Default: 127.0.0.1:7861 (localhost only)
```

The Gradio UI binds to localhost by default to prevent accidental network exposure.

**To expose on network:**
```bash
# Set host (required)
export COMFY_HEADLESS_UI__HOST=0.0.0.0

# Set authentication (strongly recommended)
export COMFY_HEADLESS_UI__USERNAME=admin
export COMFY_HEADLESS_UI__PASSWORD=your-secure-password
```

**Warning:** Never expose the UI on a network without authentication. A warning is emitted if you set `HOST=0.0.0.0` without credentials.

### WebSocket Connections

```
Default: Requires wss:// (encrypted) for non-localhost connections
```

WebSocket connections to remote ComfyUI servers require encryption by default.

**For localhost (development):**
- `ws://localhost:8188` - Allowed (unencrypted OK for development)
- `ws://127.0.0.1:8188` - Allowed

**For remote hosts (production):**
- `wss://comfyui.example.com` - Allowed (encrypted)
- `ws://comfyui.example.com` - **Blocked by default**

**To allow insecure remote connections (not recommended):**
```bash
export COMFY_HEADLESS_WEBSOCKET__ALLOW_INSECURE=true
```

### HTTPS/WSS in Production

Always use HTTPS/WSS in production:

```python
# Production configuration
os.environ["COMFY_HEADLESS_COMFYUI__URL"] = "https://comfyui.internal:8188"
# WebSocket will automatically use wss://
```

## Security Best Practices

### Configuration

```python
# Use environment variables for sensitive config
import os
os.environ["COMFY_HEADLESS_COMFYUI__URL"] = "http://localhost:8188"

# Never hardcode credentials
# BAD: client = ComfyClient(api_key="sk-12345")
# GOOD: Use environment variables or secrets manager
```

### Network Security

1. **Run ComfyUI on localhost** or trusted internal networks
2. **Use HTTPS/WSS** in production environments
3. **Use a reverse proxy** (nginx, Caddy) with authentication for external access
4. **Firewall rules** - Block port 8188 from external access

### Reverse Proxy Example (nginx)

```nginx
server {
    listen 443 ssl;
    server_name comfyui.example.com;

    ssl_certificate /etc/ssl/certs/comfyui.crt;
    ssl_certificate_key /etc/ssl/private/comfyui.key;

    location / {
        auth_basic "ComfyUI";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8188;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Input Validation

comfy-headless validates inputs by default, but ensure:
- User-provided prompts are sanitized before display
- File paths don't allow directory traversal
- Dimensions are within reasonable bounds (max 2048x2048)

### Secrets

```python
# pydantic SecretStr masks secrets in logs/repr
# Password configured via environment is automatically handled
os.environ["COMFY_HEADLESS_UI__PASSWORD"] = "secret123"

# In config, password is SecretStr type
from comfy_headless.config import get_settings
cfg = get_settings()
print(cfg.ui.password)  # Output: SecretStr('**********')
```

## Known Security Considerations

### WebSocket Connections

- WebSocket connections to ComfyUI are not encrypted by default
- Use WSS (WebSocket Secure) in production
- Client IDs are UUIDs, not authentication tokens
- Non-localhost unencrypted connections are blocked by default

### Temporary Files

- Generated images are stored in temp directories
- Automatic cleanup runs periodically
- Set `COMFY_HEADLESS_UI__TEMP_CLEANUP_INTERVAL` for custom cleanup (seconds)

### Logging

- Debug logs may contain sensitive information
- Set `COMFY_HEADLESS_LOGGING__LEVEL=INFO` or higher in production
- Secrets (SecretStr) are masked automatically
- Avoid logging user data unnecessarily

### Rate Limiting

- No built-in rate limiting (ComfyUI handles queue)
- Consider implementing rate limiting at reverse proxy level
- Circuit breaker is enabled by default for connection failures

## Security Updates

Security updates are released as patch versions (e.g., 2.5.1 -> 2.5.2).

To stay updated:
1. Watch this repository for releases
2. Use `pip install --upgrade comfy-headless`
3. Subscribe to security advisories on GitHub

### Recent Security Fixes

| Version | Fix |
|---------|-----|
| 2.5.1 | UI binds to localhost by default |
| 2.5.1 | WebSocket rejects unencrypted remote connections by default |
| 2.5.1 | Added UI authentication support |
| 2.5.0 | Gradio >=5.6.0 required (CVE-2025-23042 fix) |

## Compatibility Policy

- **Python**: 3.10, 3.11, 3.12 (tested in CI)
- **ComfyUI**: Latest stable (best effort compatibility)
- **Gradio**: >=5.6.0 (security requirement)

We follow semantic versioning:
- MAJOR: Breaking changes
- MINOR: New features, backwards compatible
- PATCH: Bug fixes, security updates
