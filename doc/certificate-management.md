# Stalwart Certificate Management

## Overview

Stalwart provides comprehensive certificate management capabilities through its HTTP API and CLI tools. This document covers certificate reloading, ACME support, and programmatic certificate management.

**Official Documentation:**
- [ACME Configuration](https://stalw.art/docs/category/acme/) - Automatic certificate management with Let's Encrypt
- [TLS Configuration](https://stalw.art/docs/server/tls/overview) - TLS settings and certificate setup
- [Reverse Proxy Setup](https://stalw.art/docs/server/reverse-proxy/overview) - Nginx, HAProxy, and proxy protocol configuration

## Quick Reference

**Common Questions:**

| Question | Answer |
|----------|--------|
| Can I use dots in certificate IDs? | **Yes** - `certificate.mail.example.com.cert` is valid |
| Do I need to restart after updating certs? | **No** - Use `stalwart-cli server reload-certificates` (zero downtime) |
| When are `%{file:...}%` macros expanded? | **At startup and reload** - not continuously, must reload after file changes |
| What does `list-config` show? | **Raw stored values** with unexpanded macros like `%{file:...}%` |
| How many certificates should have `default = true`? | **Only ONE** - it's the fallback for non-SNI clients |
| Should I create separate certs per subdomain? | **No** - Use one cert with SANs for all domains (simpler & better) |

**Syntax Examples:**
```toml
# Recommended: File reference with macro
certificate.default.cert = "%{file:/opt/stalwart/certs/fullchain.pem}%"
certificate.default.private-key = "%{file:/opt/stalwart/certs/privkey.pem}%"
certificate.default.default = true

# Using domain as ID (dots allowed)
certificate.mail.example.com.cert = "%{file:/opt/stalwart/certs/mail.example.com.pem}%"
```

## Certificate Reloading

### API Endpoint
- **Endpoint**: `GET /api/reload/certificate`
- **Purpose**: Reloads TLS certificates without server restart
- **Authentication**: Requires admin privileges with `SettingsReload` permission

### CLI Command
```bash
stalwart-cli -c admin:yourpassword -u http://127.0.0.1 server reload-certificates
```

### Direct API Call
```bash
curl -X GET \
  -H "Authorization: Basic $(echo -n 'admin:yourpassword' | base64)" \
  -H "Content-Type: application/json" \
  "http://127.0.0.1/api/reload/certificate"
```

### Use Case
Perfect for automated certificate renewal scripts (e.g., Let's Encrypt) to update certificates without service interruption.

## ACME (Automatic Certificate Management Environment)

Stalwart provides built-in ACME support for automatic certificate provisioning and renewal.

**See official documentation:** [ACME Configuration Guide](https://stalw.art/docs/category/acme/)

### Supported Challenge Types
- `TLS-ALPN-01`
- `DNS-01`
- `HTTP-01`

### Supported DNS Providers
- Cloudflare
- DigitalOcean
- OVH
- DeSEC
- Custom DNS providers

### Configuration Keys
- `acme.*`
- `acme.<id>.directory` - ACME directory URL (e.g., Let's Encrypt endpoints)
- `acme.<id>.contact` - Contact email addresses
- `acme.<id>.domains` - Domains to cover
- `acme.<id>.challenge` - Challenge type to use
- `acme.<id>.provider` - DNS provider
- `acme.<id>.secret` - API credentials
- `acme.<id>.renew-before` - Renewal timing

## Alternative: Using acme.sh for Certificate Management

For users who prefer external certificate management tools or are already using acme.sh for other services, acme.sh provides an excellent alternative to Stalwart's built-in ACME support.

### Benefits of acme.sh
- Proven reliability across many platforms (Zimbra, Stalwart, etc.)
- Works with any DNS provider (DNS-01 challenge)
- Automatic renewal via cron
- Single tool for managing certificates across multiple services
- Custom deploy hooks for seamless integration

### Quick Setup

1. **Install acme.sh** (one-time):
   ```bash
   curl https://get.acme.sh | sh -s email=your@email.com
   ```

2. **Configure Let's Encrypt** (one-time):
   ```bash
   acme.sh --set-default-ca --preferred-chain "ISRG" --server letsencrypt
   ```

3. **Issue certificate** (using Cloudflare DNS-01 as example):
   ```bash
   acme.sh --issue --dns dns_cf -d mail.example.com -d example.com -d smtp.example.com
   ```

4. **Deploy to Stalwart** (using custom deploy hook):
   ```bash
   acme.sh --deploy --deploy-hook stalwart -d mail.example.com
   ```

5. **Automatic renewal**: acme.sh installs a cron job automatically:
   ```cron
   39 7 * * * "/home/user/.acme.sh"/acme.sh --cron --home "/home/user/.acme.sh" > /dev/null
   ```

### Stalwart Deploy Hook

A custom deploy hook for Stalwart is available at:
- [acme.sh stalwart deploy hook](https://github.com/JimDunphy/acme.sh/blob/master/deploy/stalwart.sh)

The deploy hook handles:
- Installing certificates to the correct location
- Triggering certificate reload via Stalwart API (zero downtime)
- Proper file permissions

**Additional Resources:**
- [acme.sh Documentation](https://github.com/acmesh-official/acme.sh)
- [DNS API Integration Guide](https://github.com/acmesh-official/acme.sh/wiki/dnsapi)
- Zimbra wiki articles by JDunphy for additional deployment examples

## Other Certificate-Related APIs

### Configuration Management
- `GET /api/settings/list?prefix=certificate` - List all certificate configurations
- `POST /api/settings` - Update certificate configurations using UpdateSettings structure
- `DELETE /api/settings/{prefix}` - Delete certificate configurations

### UpdateSettings Structure
```json
[
  {
    "type": "insert|delete|clear",
    "prefix": "certificate.my-cert",
    "values": [
      ["cert", "-----BEGIN CERTIFICATE-----..."],
      ["key", "-----BEGIN PRIVATE KEY-----..."]
    ],
    "keys": ["certificate.my-cert.cert", "certificate.my-cert.key"]
  }
]
```

### S/MIME Certificate Management
- `/api/account/crypto` - Manage user S/MIME certificates for email encryption at rest

## Best Practices for Certificate Renewal

### 1. Use the reload endpoint instead of restarting the service
```bash
# GOOD - Zero downtime
stalwart-cli -c admin:yourpassword -u http://127.0.0.1 server reload-certificates

# AVOID - Service interruption
systemctl restart stalwart
```

### 2. Use dedicated API credentials
For automation scripts, consider creating an API user with only `SettingsReload` permission instead of using your main admin account for security.

### 3. Verify certificate reload success
Both the CLI command and API call return a JSON response with the updated configuration data.

## Certificate Configuration

### Configuration Pattern

Certificates are configured using the pattern `certificate.<id>.*` where `<id>` is a unique identifier for the certificate.

**Allowed characters in `<id>`:**
- Alphanumeric: `a-z`, `A-Z`, `0-9`
- Special characters: `.` (dot), `-` (hyphen), `_` (underscore)
- **Dots are allowed**, enabling patterns like: `certificate.mail.example.com.cert`

### Configuration Methods

#### Method 1: File References (Recommended)

Use the `%{file:...}%` macro to load certificates from disk:

```toml
# Flattened format
certificate.default.cert = "%{file:/opt/stalwart/etc/certs/fullchain.pem}%"
certificate.default.private-key = "%{file:/opt/stalwart/etc/certs/privkey.pem}%"
certificate.default.default = true

# Or using domain as ID (dots allowed)
certificate.mail.example.com.cert = "%{file:/opt/stalwart/etc/certs/mail.example.com/fullchain.pem}%"
certificate.mail.example.com.private-key = "%{file:/opt/stalwart/etc/certs/mail.example.com/privkey.pem}%"

# Or table format (equivalent)
[certificate.default]
cert = "%{file:/opt/stalwart/etc/certs/fullchain.pem}%"
private-key = "%{file:/opt/stalwart/etc/certs/privkey.pem}%"
default = true
```

#### Method 2: Inline PEM Content

Embed certificate content directly in configuration:

```toml
[certificate.default]
cert = """-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKZ...
-----END CERTIFICATE-----"""
private-key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w...
-----END PRIVATE KEY-----"""
default = true
```

### Default Certificate Behavior

**Important:** Only ONE certificate should be marked with `default = true`.

The default certificate is used when:
1. Client doesn't support SNI (Server Name Indication)
2. Client connects without providing SNI (e.g., by IP address)
3. Client provides SNI that doesn't match any certificate's subject/SAN names

```toml
# Correct: Only one default
certificate.default.default = true

# Wrong: Multiple defaults causes undefined behavior
certificate.cert1.default = true
certificate.cert2.default = true  # DON'T DO THIS
```

### Best Practice: Use SANs (Subject Alternative Names)

Instead of creating separate certificates for each subdomain, use ONE certificate with multiple SANs:

```toml
# Recommended: Single certificate with SANs for all domains
certificate.default.cert = "%{file:/opt/stalwart/certs/fullchain.pem}%"
certificate.default.private-key = "%{file:/opt/stalwart/certs/privkey.pem}%"
certificate.default.default = true
```

Where the certificate includes SANs for:
- `example.com`
- `mail.example.com`
- `smtp.example.com`
- `imap.example.com`
- `mta-sts.example.com`

This approach:
- Simplifies configuration
- Works correctly for both SNI and non-SNI clients
- Reduces certificate management overhead
- Follows industry best practices

**See also:** [TLS Configuration Overview](https://stalw.art/docs/server/tls/overview) for more details on certificate setup.

## Troubleshooting Certificate Issues

### Common Problems

#### 1. Certificate File Not Loading

**Symptoms:**
- TLS handshake failures
- "No certificates found" errors
- Clients can't connect with TLS

**Check the logs for configuration errors:**

```bash
# Search for macro expansion errors (systemd installations)
journalctl -u stalwart -n 500 | grep -i "macro"

# Search for certificate parsing errors
journalctl -u stalwart -n 500 | grep -i "certificate"

# Or check the Stalwart log file directly
grep -i "macro\|certificate" /opt/stalwart/logs/stalwart.log
```

**Configuration error types** (see `crates/utils/src/config/mod.rs:log_errors()`):

| Error Type | Cause | Example Message |
|------------|-------|-----------------|
| `MacroError` | Failed to read file or expand macro | `Macro expansion error for setting "certificate.default.cert": Failed to read file "/path/to/cert.pem": No such file or directory` |
| `ParseError` | Invalid configuration syntax | `Failed to parse setting "certificate.default.cert": ...` |
| `BuildError` | Configuration build failure | `Build error for key "certificate.default.cert": ...` |

#### 2. File Permission Issues

**Symptoms:**
- MacroError with "Permission denied"

**Fix:**
```bash
# Verify Stalwart can read the certificate files
sudo -u stalwart cat /opt/stalwart/certs/fullchain.pem

# If permission denied, fix ownership or permissions
sudo chown stalwart:stalwart /opt/stalwart/certs/*.pem
sudo chmod 644 /opt/stalwart/certs/fullchain.pem
sudo chmod 600 /opt/stalwart/certs/privkey.pem  # Private key should be restrictive
```

**Note:** Stalwart does **not** reject certificates with overly permissive permissions (e.g., world-readable). However, best practice is to restrict private key access to 600.

#### 3. Wrong File Path

**Symptoms:**
- MacroError with "No such file or directory"

**Verify:**
```bash
# Check file exists
ls -la /opt/stalwart/certs/fullchain.pem

# Check path in configuration
stalwart-cli server list-config | grep certificate

# Remember: list-config shows unexpanded macros
# Example output: certificate.default.cert = "%{file:/opt/stalwart/certs/fullchain.pem}%"
```

#### 4. Invalid PEM Format

**Symptoms:**
- "No certificates found" or "Failed to read certificates"
- Parsing errors in logs

**Verify certificate format:**
```bash
# Check file type
file /opt/stalwart/certs/fullchain.pem
# Should output: "PEM certificate" or "ASCII text"

# Verify it's valid PEM
openssl x509 -in /opt/stalwart/certs/fullchain.pem -noout -text

# Check for BOM or corruption at file start
hexdump -C /opt/stalwart/certs/fullchain.pem | head -3
# Should start with: 2d 2d 2d 2d 2d 42 45 47 49 4e (-----BEGIN)
```

**Common format issues:**
- DER format instead of PEM (binary file)
- PKCS12/PFX format (.pfx, .p12) - needs conversion
- JKS format (.jks) - Java keystore, needs conversion
- Certificate with BOM (Byte Order Mark) at start
- Wrong file (CSR instead of certificate)

**Convert DER to PEM:**
```bash
openssl x509 -inform DER -in cert.der -out cert.pem
```

**Convert PFX to PEM:**
```bash
# Extract certificate
openssl pkcs12 -in cert.pfx -clcerts -nokeys -out cert.pem

# Extract private key
openssl pkcs12 -in cert.pfx -nocerts -nodes -out privkey.pem
```

#### 5. Certificate/Private Key Mismatch

**Symptoms:**
- TLS handshake errors: "DecryptError", "UnexpectedMessage"
- Connections fail after reload

**Verify certificate and key match:**
```bash
# Get certificate modulus
openssl x509 -noout -modulus -in /opt/stalwart/certs/fullchain.pem | openssl md5

# Get private key modulus
openssl rsa -noout -modulus -in /opt/stalwart/certs/privkey.pem | openssl md5

# The MD5 hashes MUST match
```

#### 6. Macro Syntax Errors

**Wrong syntax (won't work):**
- `certificate.default.cert = "file:///opt/stalwart/certs/cert.pem"` ❌
- `certificate.default.cert = "%file:/opt/stalwart/certs/cert.pem%"` ❌ (missing braces)
- `certificate.default.cert = "${file:/opt/stalwart/certs/cert.pem}"` ❌ (wrong delimiter)

**Correct syntax:**
- `certificate.default.cert = "%{file:/opt/stalwart/certs/cert.pem}%"` ✅

### Debug Checklist

When certificates aren't loading, check in this order:

1. ✅ **Check logs** for MacroError/ParseError messages
2. ✅ **Verify file exists** at the exact path specified
3. ✅ **Test file permissions** - can Stalwart user read it?
4. ✅ **Verify PEM format** - use `openssl x509 -text`
5. ✅ **Check cert/key match** - compare modulus hashes
6. ✅ **Verify macro syntax** - must be `%{file:...}%`
7. ✅ **Reload certificates** - `stalwart-cli server reload-certificates`
8. ✅ **Check reload success** - look for errors in response/logs

## Configuration Storage

Certificate configurations are stored in the database (or configuration store) using keys with the pattern `certificate.*` and are loaded into memory at runtime.

### Viewing Stored Configuration

```bash
stalwart-cli server list-config | grep certificate
```

**Important:** `list-config` displays **raw stored values**, including unexpanded macros like `%{file:...}%`. The actual certificate content is only loaded when the configuration is built (at startup or reload).

## Implementation Details

### Macro Expansion Timing

The `%{file:...}%` macro is expanded **at configuration build time**, not at storage time:

1. **At Server Startup**: `Config::build_config()` is called, which:
   - Loads configuration from storage
   - Calls `config.resolve_all_macros().await` (see `crates/utils/src/config/mod.rs:70-171`)
   - Reads file contents from disk
   - Expands environment variables
   - Builds the final configuration in memory

2. **At Reload**: Same process - macros are re-expanded with current values:
   - `stalwart-cli server reload-certificates` triggers reload
   - File contents are re-read from disk
   - Updated certificates become active without restart

**Key insight:** When you update a certificate file on disk, you **must reload** for Stalwart to read the new content. The macro is not continuously evaluated.

### Certificate Reloading Mechanism

The certificate reloading works as follows:
1. Stalwart server receives API call to `/api/reload/certificate` (see `crates/http/src/management/reload.rs:59-62`)
2. Server calls `reload_certificates()` function (see `crates/common/src/manager/reload.rs:42-50`)
3. Configuration is rebuilt (macros expanded from storage)
4. Certificates are parsed using `parse_certificates()` (see `crates/common/src/config/server/tls.rs:318-415`)
5. Certificate IDs are extracted via `config.sub_keys("certificate", ".cert")` (see `crates/utils/src/config/utils.rs:107-130`)
6. PEM data is parsed using `rustls_pemfile::certs()` (see `crates/common/src/config/server/tls.rs:418`)
7. In-memory certificate store is atomically updated using ArcSwap
8. New certificates are available immediately without restart

This approach ensures zero downtime and immediate certificate availability.

### Configuration Parsing Details

**Certificate ID Extraction** (`crates/utils/src/config/utils.rs:107-130`):
- Pattern `certificate.<id>.cert` is parsed
- Prefix `"certificate."` is stripped
- Suffix `".cert"` is stripped
- Everything between becomes the certificate ID
- Example: `certificate.mail.example.com.cert` → ID is `mail.example.com`

**File Macro Reading** (`crates/utils/src/config/mod.rs:117-122`):
- Files are read with `tokio::fs::read(file_name).await`
- Content is converted to UTF-8 string
- Entire file content (including trailing newlines) is inserted into config value
- No trimming is performed (certificates handle trailing whitespace gracefully)

## Key Rust Implementation Files

For developers wanting to understand the implementation in detail, here are the key Rust source files:

### CLI Implementation
- `crates/cli/src/main.rs` - Main CLI entry point
- `crates/cli/src/modules/cli.rs` - Command definitions including `ServerCommands::ReloadCertificates`
- `crates/cli/src/modules/database.rs` - Implementation of server commands, including the reload-certificates handler

### HTTP API Implementation
- `crates/http/src/management/reload.rs` - HTTP handler for `/api/reload/certificate` endpoint
- `crates/http/src/management/mod.rs` - Main management API routing
- `crates/http/src/management/settings.rs` - Configuration management endpoints

### Certificate Loading and Parsing
- `crates/common/src/manager/reload.rs` - Core `reload_certificates()` function implementation
- `crates/common/src/config/server/tls.rs` - Certificate parsing logic with `parse_certificates()` function
- `crates/common/src/listener/tls.rs` - TLS listener implementation

### ACME Support
- `crates/common/src/listener/acme/mod.rs` - ACME provider management
- `crates/common/src/listener/acme/directory.rs` - ACME directory and challenge handling
- `crates/common/src/listener/acme/resolver.rs` - ACME certificate resolver
- `crates/services/src/housekeeper/mod.rs` - ACME certificate renewal scheduling

### Configuration Management
- `crates/common/src/config/inner.rs` - Configuration loading and parsing
- `crates/common/src/listener/listen.rs` - TLS connection handling

## Additional Certificate-Related API Endpoints

### Configuration Management
- `GET /api/settings/list?prefix=certificate` - List all certificate configurations
- `GET /api/settings/keys?prefixes=certificate` - Get specific certificate configuration keys
- `POST /api/settings` - Update certificate configurations (requires admin privileges)
- `DELETE /api/settings/certificate.{id}` - Delete certificate configurations

### S/MIME Management
- `GET /api/account/crypto` - Retrieve S/MIME encryption settings for current account
- `POST /api/account/crypto` - Update S/MIME encryption settings

### Certificate Information and Troubleshooting
- `GET /api/troubleshoot/tls` - TLS connection troubleshooting information
- `GET /api/dns/certificate` - Certificate-related DNS information

### Server Management
- `GET /api/reload` - Reload entire configuration (including certificates)
- `GET /api/healthz/ready` - Server readiness check
- `GET /api/healthz/live` - Server liveness check

### Permission Requirements
All certificate-related API endpoints require appropriate permissions:
- `SettingsReload` for certificate reloading
- `SettingsList` for listing configurations
- `SettingsUpdate` for updating configurations
- `SettingsDelete` for deleting configurations
- `ManageEncryption` for S/MIME operations