# Authentication

Understand how **lmi** handles authentication. This includes:
- **User SSO Authentication**: For users to log in interactively via the company's Single Sign-On (SSO) using PKCE flow.
- **Service Authentication**: OAuth flows (Client Credentials, Password Grant, Authorization Code + PKCE) for authenticating the CLI to specific backend services based on environment configuration.

This document covers both, focusing on how tokens are acquired, cached, and used.

## 1. Supported OAuth Flows

The CLI supports multiple OAuth grant types, configurable per environment:

- **Client Credentials Grant**: For service-to-service authentication.
- **Password Grant**: For user-based authentication (not recommended for production).
- **Authorization Code + PKCE**: For secure user authentication with SSO integration.

The grant type is configured using the `OAUTH_GRANT_TYPE` environment variable or config setting:
```bash
# For service-to-service auth
OAUTH_GRANT_TYPE=client_credentials

# For user password auth (not recommended)
OAUTH_GRANT_TYPE=password

# For SSO/PKCE auth
OAUTH_GRANT_TYPE=authorization_code_pkce
```

## 2. Token Management

### Token Storage
- All tokens are stored in `~/.cache/lmi/tokens/<env_name>.json` (or OS-appropriate location).
- Tokens are stored using the `AuthToken` dataclass format, which includes:
  - `access_token`: The OAuth access token
  - `refresh_token`: Optional refresh token for token renewal
  - `id_token`: Optional ID token for user information
  - `expires_at`: Token expiration timestamp
  - `token_type`: Token type (usually "Bearer")
  - `issued_at`: Token issuance timestamp

### Token Refresh
- Before making requests, lmi checks for a valid, non-expired cached token.
- If a token is expired but has a refresh token, it will be automatically refreshed.
- On receiving a 401 Unauthorized, lmi will:
  1. Attempt to refresh the token if a refresh token is available
  2. If refresh fails or no refresh token exists, acquire a new token
  3. Retry the original request once with the new token

## 3. User SSO Authentication (PKCE Flow)

The PKCE (Proof Key for Code Exchange) flow provides secure user authentication:

1. **Login Command**: 
   ```bash
   lmi auth login -e <env_name>
   ```
   This initiates the PKCE flow:
   - Generates a code verifier and challenge
   - Opens your browser to the SSO login page
   - Starts a local HTTP server to receive the callback
   - Exchanges the authorization code for tokens

2. **Token Storage**: 
   - Successfully obtained tokens are stored in the token cache
   - Includes access token, refresh token, and ID token
   - Tokens are automatically refreshed when expired

3. **Logout Command**: 
   ```bash
   lmi auth logout -e <env_name>
   ```
   This clears the cached tokens for the specified environment.

4. **Status Command**: 
   ```bash
   lmi auth status -e <env_name>
   ```
   Shows your current authentication status and token information.

## 4. Environment-Specific Authentication

Each environment can use a different authentication method:

```bash
# Development environment using client credentials
[dev]
OAUTH_GRANT_TYPE=client_credentials
OAUTH_CLIENT_ID=dev-client
OAUTH_CLIENT_SECRET=dev-secret
OAUTH_TOKEN_URL=https://dev.example.com/token

# Production environment using PKCE
[prod]
OAUTH_GRANT_TYPE=authorization_code_pkce
OAUTH_CLIENT_ID=prod-client
OAUTH_AUTHORIZE_URL=https://prod.example.com/authorize
OAUTH_TOKEN_URL=https://prod.example.com/token
```

## 5. Security Best Practices

- Store secrets (client secrets, passwords) in environment variables or env-specific `.env` files.
- Do not store secrets in the main `.env` or pass them on the command line.
- The token cache directory (`~/.cache/lmi/tokens/`) should have restricted permissions.
- For PKCE flow, ensure your browser's security settings allow localhost callbacks.
- Regularly rotate client secrets and credentials.
- Use environment-specific configurations to separate development and production credentials.

## 6. Troubleshooting Authentication

### Common Issues

1. **Token Expiration**:
   - Symptoms: 401 Unauthorized errors
   - Solution: Run `lmi auth login -e <env_name>` to re-authenticate

2. **PKCE Flow Issues**:
   - Browser doesn't open: Check `OAUTH_AUTHORIZE_URL` configuration
   - Callback fails: Ensure no firewall is blocking localhost
   - Token exchange fails: Verify `OAUTH_TOKEN_URL` and client configuration

3. **Token Cache Issues**:
   - Corrupted cache: Delete `~/.cache/lmi/tokens/<env_name>.json`
   - Permission issues: Check directory permissions
   - Invalid tokens: Run `lmi auth logout -e <env_name>` then login again

### Debugging

- Use `-v` or `-vv` for detailed logging
- Check token status: `lmi auth status -e <env_name>`
- Verify configuration: `lmi config show -e <env_name>`
- For SSO issues, ensure you can log into your IdP via browser
- Check logs for specific error messages

For more technical details, see the [Development Guide](development-guide.md). 