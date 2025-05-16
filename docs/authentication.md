# Authentication

Understand how **lmi** handles authentication. This includes:
- **User SSO Authentication**: For users to log in interactively via the company's Single Sign-On (SSO) to authorize CLI usage.
- **Service Authentication**: OAuth flows (like Client Credentials) for authenticating the CLI to specific backend services based on environment configuration.

This document covers both, focusing on how tokens are acquired, cached, and used.

## 1. Supported OAuth Flows

- **Client Credentials Grant**: For service-to-service authentication.
- **Password Grant**: For user-based authentication (not recommended for production).
- Other flows (e.g., Authorization Code + PKCE) are not supported in the MVP.

Authentication is triggered automatically based on your resolved configuration.

## 2. Token Caching and Refresh

### Service Tokens
- Tokens for service authentication (Client Credentials, Password Grant) are cached in `~/.cache/lmi/tokens/<env_name>.json` (or OS-appropriate location).
- Before making requests to a service, lmi checks for a valid, non-expired cached token for that environment.
- If a valid token is found, it is used. Otherwise, a new token is acquired based on the environment's configuration.
- On receiving a 401 Unauthorized from a service, lmi discards the cached service token, acquires a new one, and retries once.
- If service token refresh fails, a clear error is reported.

### User SSO Tokens
- Details about User SSO Authentication, including its own token management (using the OS keychain), are described in [User SSO Authentication](#3-user-sso-authentication).

## 3. User SSO Authentication

To ensure that only authorized company personnel can perform sensitive operations via the `lmi` CLI, an interactive SSO login flow is provided.
- **Login Command**: `lmi login sso` (or similar) initiates a browser-based authentication with your company's IdP.
- **Token Storage**: Successfully obtained SSO tokens (access, refresh, ID tokens) are stored securely in your operating system's keychain.
- **Purpose**: A valid SSO session is a prerequisite for certain CLI commands or plugin features. This is independent of the service-specific authentication configured per environment.
- **Logout Command**: `lmi logout sso` (or similar) clears your SSO session and tokens from the keychain.
- **Status Command**: `lmi auth status` (or similar) shows your current SSO login status.

For detailed technical specifications, see `docs/development/specs/spec-sso-login.md`.

## 4. Security Best Practices

- Store secrets (client secrets, passwords) in environment variables or env-specific `.env` files.
- Do not store secrets in the main `.env` or pass them on the command line unless necessary.
- You are responsible for securing your `.env` and token cache files.
- lmi does not prompt for service secrets interactively; missing secrets result in errors. The SSO login flow is interactive via the browser.

## 5. Troubleshooting Authentication

- If you see authentication errors, check that your environment config has the correct client ID, secret, and service URL.
- Ensure your token cache file is not corrupted or expired.
- Use `-v` or `-vv` for more detailed error output.
- If you need to clear the **service token cache**, delete the relevant file in `~/.cache/lmi/tokens/`.
- For SSO issues, ensure you can log into your company's IdP via a browser. Use `lmi auth status` (or similar) to check your SSO login status. If problems persist, consult your IdP administrator or the `lmi` documentation (`docs/development/specs/spec-sso-login.md`). 