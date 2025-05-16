---
description: "Defines the interactive SSO login mechanism for the lmi CLI, enabling user authentication via a company IdP to gate access to sensitive operations."
globs: ""
alwaysApply: false
---

# lmi CLI Specification: Interactive SSO Login

## 1. Scope and Rationale

This specification details the addition of an interactive Single Sign-On (SSO) login flow to the `lmi` CLI. The primary goal is to allow users to authenticate against the company's central Identity Provider (IdP) using a browser-based flow. A successful SSO login will result in a locally stored user-specific token (or set of tokens) that can be used by the CLI core to gate access to certain commands or plugin functionalities, ensuring that only authenticated company users can perform sensitive operations.

This mechanism is inspired by patterns like `aws sso login` and complements the existing environment-specific OAuth flows (Client Credentials, Password Grant) by providing a primary user authentication layer.

## 2. Detailed Requirements and Design

### 2.1. New CLI Commands

The following new commands will be added to the `lmi` CLI, likely under an `auth` or `login` group (e.g., `lmi auth sso-login` or `lmi login` if it becomes the primary login method):

*   **`lmi login sso` (or `lmi sso login`)**:
    *   Initiates the interactive SSO authentication flow.
    *   On success, stores the obtained tokens securely using the OS keychain.
    *   If already logged in and tokens are valid, it may offer to re-authenticate or confirm current status.
*   **`lmi logout sso` (or `lmi sso logout`)**:
    *   Clears the SSO tokens from the OS keychain.
    *   Invalidates the user's SSO session with the CLI.
*   **`lmi auth status` (or `lmi sso status`)**:
    *   Displays the current SSO login status (e.g., "Logged in as user@example.com, session valid until YYYY-MM-DD HH:MM:SS" or "Not logged in via SSO.").
    *   May show additional details like the user identifier from the token if available.

### 2.2. Authentication Flow: OAuth 2.0 Authorization Code Grant with PKCE

The Authorization Code Grant with PKCE (Proof Key for Code Exchange) is the recommended flow for a CLI application.

**Steps:**

1.  **Initiation (`lmi login sso` execution):**
    *   The CLI generates a cryptographically random `code_verifier`.
    *   The CLI derives a `code_challenge` from the `code_verifier` (using S256 method).
    *   The CLI constructs an authorization URL pointing to the company's IdP. This URL will include:
        *   `response_type=code`
        *   `client_id` (a pre-configured ID for the `lmi` CLI application, registered with the IdP)
        *   `redirect_uri` (a local URI, e.g., `http://localhost:PORT/callback`, where `PORT` is a temporarily available port)
        *   `scope` (e.g., `openid profile email offline_access` - to get an ID token, user info, and a refresh token)
        *   `code_challenge`
        *   `code_challenge_method=S256`
        *   `state` (an opaque value for CSRF protection)
    *   The CLI opens the user's default web browser to this authorization URL.
    *   The CLI starts a temporary local HTTP server listening on the `redirect_uri`'s port.

2.  **User Authentication at IdP:**
    *   The user authenticates with the IdP in their browser (e.g., enters SSO credentials, MFA).

3.  **Redirection to CLI:**
    *   Upon successful authentication, the IdP redirects the user's browser back to the `redirect_uri` specified by the CLI. The redirect will include an `authorization_code` and the `state` value.

4.  **Callback Handling by CLI:**
    *   The local HTTP server captures the `authorization_code` and `state`.
    *   The CLI verifies that the received `state` matches the one sent initially.
    *   The local server should ideally shut down after successfully capturing the code or after a timeout.

5.  **Token Exchange:**
    *   The CLI makes a POST request to the IdP's token endpoint. This request includes:
        *   `grant_type=authorization_code`
        *   `code` (the received authorization code)
        *   `redirect_uri` (the same one used in step 1)
        *   `client_id`
        *   `code_verifier` (the original secret verifier)
    *   The IdP validates the request and, if successful, returns a JSON response containing:
        *   `access_token`
        *   `refresh_token` (if `offline_access` scope was requested)
        *   `id_token` (if `openid` scope was requested)
        *   `expires_in`
        *   `token_type` (typically "Bearer")

### 2.3. Token Storage

*   **Primary User SSO Tokens (Access Token, Refresh Token, ID Token):**
    *   These tokens MUST be stored securely using the operating system's native keychain/credential manager (e.g., macOS Keychain, Windows Credential Manager, Freedesktop Secret Service on Linux).
    *   The Python `keyring` library should be used for this purpose.
    *   This supersedes the previous note in `prd.md` about keyring being a future consideration; it is now a requirement for this SSO feature.
*   **Service-Specific Tokens (e.g., from Client Credentials flow for a particular environment):**
    *   These will continue to be cached as per the existing mechanism (`~/.cache/lmi/tokens/<env_name>.json`), as they are typically tied to an environment/service principal rather than an individual user's interactive session.

### 2.4. Token Usage and Gating Access

*   **CLI Core Check:** Before executing commands or plugin operations deemed sensitive or requiring company user authentication, the `lmi` core will check for the presence and validity (e.g., not expired) of the user's SSO access token from the keychain.
*   **Validity Check:**
    *   The `access_token`'s expiry will be checked.
    *   If expired, the CLI will attempt to use the `refresh_token` (if available) to silently obtain a new set of tokens from the IdP. This refresh should also update the tokens in the keychain.
    *   If refresh fails or no refresh token is available, the user must be prompted to run `lmi login sso` again.
*   **Plugin Interaction:**
    *   The `CliContext` provided to plugins could include a flag or method indicating the user's SSO authentication status (e.g., `context.is_sso_authenticated() -> bool`, `context.get_sso_user_info() -> Optional[dict]`).
    *   Plugins can then use this information to conditionally enable/disable specific commands or features.
    *   Alternatively, the CLI core could enforce this check before dispatching to certain registered plugin commands based on a new metadata attribute defined by plugins (e.g., `requires_sso=True`).

### 2.5. Configuration

*   **`OAUTH_SSO_CLIENT_ID`**: The OAuth client ID for the `lmi` CLI application, registered with the company IdP for the interactive SSO flow.
*   **`OAUTH_SSO_AUTHORIZATION_URL`**: The IdP's authorization endpoint.
*   **`OAUTH_SSO_TOKEN_URL`**: The IdP's token endpoint.
*   **`OAUTH_SSO_SCOPES`**: Scopes to request (e.g., "openid profile email offline_access").
    These will be part of the global CLI configuration, likely stored in `~/.config/lmi/.env` or environment variables, similar to other OAuth settings.

### 2.6. Libraries

*   **`Authlib`**: Recommended for implementing the OAuth 2.0 Authorization Code Grant with PKCE client logic.
*   **`keyring`**: For secure storage and retrieval of SSO tokens from the OS keychain.
*   **`httpx`**: For making HTTP requests (already in use).

## 3. Security Considerations

*   **PKCE:** Essential for mitigating authorization code interception attacks in public clients like CLIs.
*   **Keychain Storage:** Storing tokens in the OS keychain is significantly more secure than plaintext files.
*   **State Parameter:** Used for CSRF protection during the browser redirect flow.
*   **Redirect URI:** Must be specific (e.g., `http://localhost:PORT/callback`) and registered with the IdP. The port should be chosen carefully to avoid conflicts and be bound only to localhost.
*   **HTTPS:** All communication with the IdP (authorization and token endpoints) MUST use HTTPS.
*   **Token Scope:** Request minimal necessary scopes.
*   **ID Token Validation:** If an ID token is received, its signature, issuer, audience, and expiry should be validated.

## 4. Developer and Plugin Support

*   The `AuthenticatedClient` in `src/lmi/auth.py` might need to be refactored or augmented. A new method or mechanism will be needed to check the SSO login status.
*   The `CliContext` object passed to plugins will be enhanced to include SSO status and potentially user information derived from the ID token.
*   Plugin developers will be provided with guidance on how to mark their commands as requiring SSO authentication if the CLI core adopts a metadata-based enforcement approach.

## 5. Impact on Existing Authentication

*   This SSO login is an *additional* authentication layer, primarily for gating user access to the CLI's capabilities.
*   Environment-specific authentication (e.g., Client Credentials for a service in `dev.env`) will still function as before. An operation might require *both* a valid user SSO session *and* valid service credentials for a specific environment.
    *   Example: `lmi --env prod create-critical-resource`
        1.  CLI checks for valid user SSO token (user is authorized to use `lmi` for `prod`).
        2.  If valid, CLI proceeds to use `prod.env` Client Credentials to authenticate to the `prod` service API to execute `create-critical-resource`.

## 6. Open Questions / Future Considerations

*   Detailed error handling for each step of the SSO flow.
*   Mechanism for plugins to declare that they require SSO.
*   Automatic token refresh retry logic and user notifications.
*   Handling IdP-specific requirements or non-standard behaviors.
*   Should `lmi logout sso` attempt to revoke tokens at the IdP (if supported)?

---
*(End of Document)* 