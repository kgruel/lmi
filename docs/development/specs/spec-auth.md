# lmi CLI Specification: Authentication and Token Management

## Scope and Rationale

This specification defines the authentication mechanisms for the `lmi` CLI, focusing on OAuth flows, token caching, and refresh logic. The goal is to automate secure authentication for users, minimize manual steps, and ensure reliable access to platform services.

## Detailed Requirements and Design

### 1. Supported OAuth Flows
- Support OAuth Client Credentials and Password Grant flows.
- Other flows (e.g., Authorization Code + PKCE) are out of scope for MVP but may be added in the future.
- Authentication is triggered automatically based on resolved configuration.

### 2. Token Caching
- Tokens are cached in `~/.cache/lmi/tokens/<env_name>.json` (or similar, following OS conventions).
- Before making requests, the CLI checks for a valid, non-expired cached token.
- Token expiry is determined by the expiry field in the token (structure to be specified).
- If a valid token is found, it is used for requests; otherwise, a new token is acquired.

### 3. Token Refresh and Error Handling
- On receiving a 401 Unauthorized response, the CLI discards the cached token, acquires a new token, and retries the request once.
- If token refresh fails, a clear error is reported to the user.
- There is no mechanism for dynamic token cache extensibility in the MVP.
- Users may request a manual cache clear in the future (open question).

### 4. Security Considerations
- Secrets (e.g., client secrets, passwords) should be sourced from OS environment variables or env-specific `.env` files.
- Token cache files are not managed for permissions by the CLI; users are responsible for securing them.
- The CLI does not prompt for secrets interactively; missing secrets result in errors.

### 5. Developer and Plugin Support
- The core provides a pre-configured, authenticated `httpx.Client` to plugin commands, handling token injection and refresh.
- Plugins should not implement their own authentication logic.

## Implementation Guidelines
- Use `httpx` for HTTP requests and token management.
- Follow OAuth 2.0 best practices for token acquisition and storage.
- Provide clear error messages for authentication failures.
- Follow PEP 8 and use type hints.
- Test token caching, expiry, and refresh logic.

## References to PRD Sections
- Functional Requirements: FR6, FR6.1, FR10, FR11
- Non-Functional Requirements: NFR5, NFR6
- Design & Architecture
- Release Criteria / MVP
- Decisions on Open Technical Questions: Token Caching & Refresh, File Security & Permissions, Keyring & Secret Management
- Remaining Open Questions: Token details (structure, expiry field), manual cache clear 