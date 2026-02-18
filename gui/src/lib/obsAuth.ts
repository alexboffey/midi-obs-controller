/**
 * Pure SHA-256 / obs-websocket v5 authentication helpers.
 * No Svelte dependencies — safe to import in unit tests.
 */

/** SHA-256 hash of a UTF-8 string, returned as base64. */
export async function sha256b64(input: string): Promise<string> {
  const data = new TextEncoder().encode(input)
  const hash = await crypto.subtle.digest('SHA-256', data)
  return btoa(String.fromCharCode(...new Uint8Array(hash)))
}

/**
 * Compute the obs-websocket v5 authentication string.
 *
 * Algorithm:
 *   secret    = base64( sha256( password + salt ) )
 *   authStr   = base64( sha256( secret + challenge ) )
 */
export async function obsAuth(
  password: string,
  salt: string,
  challenge: string,
): Promise<string> {
  const secret = await sha256b64(password + salt)
  return sha256b64(secret + challenge)
}
