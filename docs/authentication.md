# Authentication

Understand how **lmi** handles authentication, including supported OAuth flows, token caching, and security considerations.

## 1. Supported OAuth Flows

- **Client Credentials Grant**: For service-to-service authentication.
- **Password Grant**: For user-based authentication (not recommended for production).
- Other flows (e.g., Authorization Code + PKCE) are not supported in the MVP.

Authentication is triggered automatically based on your resolved configuration.

## 2. Token Caching and Refresh

- Tokens are cached in `~/.cache/lmi/tokens/<env_name>.json` (or OS-appropriate location).
- Before making requests, lmi checks for a valid, non-expired cached token.
- If a valid token is found, it is used. Otherwise, a new token is acquired.
- On receiving a 401 Unauthorized, lmi discards the cached token, acquires a new one, and retries once.
- If token refresh fails, a clear error is reported.

## 3. Security Best Practices

- Store secrets (client secrets, passwords) in environment variables or env-specific `.env` files.
- Do not store secrets in the main `.env` or pass them on the command line unless necessary.
- You are responsible for securing your `.env` and token cache files.
- lmi does not prompt for secrets interactively; missing secrets result in errors.

## 4. Troubleshooting Authentication

- If you see authentication errors, check that your environment config has the correct client ID, secret, and service URL.
- Ensure your token cache file is not corrupted or expired.
- Use `-v` or `-vv` for more detailed error output.
- If you need to clear the token cache, delete the relevant file in `~/.cache/lmi/tokens/`. 