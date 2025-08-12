/**
 * JWT Helper functions
 * Custom implementation to decode JWT tokens without external dependencies
 */

/**
 * Decode a JWT token and return its payload
 * @param token - The JWT token string
 * @returns The decoded payload object
 */
export function jwtDecode<T = any>(token: string): T {
  try {
    // JWT tokens have three parts separated by dots: header.payload.signature
    const parts = token.split('.');

    if (parts.length !== 3) {
      throw new Error('Invalid JWT token format');
    }

    // The payload is the second part (index 1)
    const payload = parts[1];

    // Decode from base64url to base64
    // Replace URL-safe characters with standard base64 characters
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');

    // Pad with '=' if necessary
    const padded = base64.padEnd(base64.length + (4 - base64.length % 4) % 4, '=');

    // Decode base64 to string
    const jsonPayload = atob(padded);

    // Parse JSON string to object
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error decoding JWT token:', error);
    throw new Error('Failed to decode JWT token');
  }
}

/**
 * Check if a JWT token is expired
 * @param token - The JWT token string
 * @returns True if the token is expired, false otherwise
 */
export function isTokenExpired(token: string): boolean {
  try {
    const decoded = jwtDecode<{ exp?: number }>(token);

    if (!decoded.exp) {
      // If there's no expiration claim, consider it as not expired
      return false;
    }

    // exp is in seconds, Date.now() is in milliseconds
    const currentTime = Date.now() / 1000;

    return decoded.exp < currentTime;
  } catch (error) {
    // If we can't decode the token, consider it as expired
    return true;
  }
}

/**
 * Get the remaining time until token expiration in seconds
 * @param token - The JWT token string
 * @returns The remaining time in seconds, or null if no expiration
 */
export function getTokenExpirationTime(token: string): number | null {
  try {
    const decoded = jwtDecode<{ exp?: number }>(token);

    if (!decoded.exp) {
      return null;
    }

    const currentTime = Date.now() / 1000;
    const remainingTime = decoded.exp - currentTime;

    return remainingTime > 0 ? remainingTime : 0;
  } catch (error) {
    return null;
  }
}

/**
 * Extract a specific claim from a JWT token
 * @param token - The JWT token string
 * @param claim - The name of the claim to extract
 * @returns The value of the claim, or undefined if not found
 */
export function getTokenClaim<T = any>(token: string, claim: string): T | undefined {
  try {
    const decoded = jwtDecode<Record<string, any>>(token);
    return decoded[claim];
  } catch (error) {
    return undefined;
  }
}

// Type definitions for common JWT claims
export interface JWTPayload {
  sub?: string;  // Subject (usually user ID)
  iat?: number;  // Issued at
  exp?: number;  // Expiration time
  nbf?: number;  // Not before
  iss?: string;  // Issuer
  aud?: string | string[];  // Audience
  jti?: string;  // JWT ID
  [key: string]: any;  // Allow additional custom claims
}

// Export default for backward compatibility
export default jwtDecode;
