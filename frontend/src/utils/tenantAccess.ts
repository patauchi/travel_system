import { store } from "../store/store";
import { jwtDecode } from "./jwtHelper";

interface TokenPayload {
  sub: string;
  email: string;
  username: string;
  role: string;
  tenant_id?: string;
  tenant_slug?: string;
  exp: number;
}

/**
 * Extract tenant slug from current URL
 */
export const getTenantFromUrl = (): string | null => {
  const hostname = window.location.hostname;
  const parts = hostname.split(".");

  // Check if we have a subdomain (e.g., tenant1.localhost or tenant1.example.com)
  if (parts.length >= 2) {
    // Don't treat 'www' as a tenant
    if (parts[0] !== "www" && parts[0] !== "localhost") {
      return parts[0];
    }
  }

  // Check URL path for tenant (e.g., /t/tenant1)
  const pathname = window.location.pathname;
  const tenantMatch = pathname.match(/^\/t\/([^/]+)/);
  if (tenantMatch) {
    return tenantMatch[1];
  }

  // Check query parameter as fallback
  const urlParams = new URLSearchParams(window.location.search);
  const tenantParam = urlParams.get("tenant");
  if (tenantParam) {
    return tenantParam;
  }

  return null;
};

/**
 * Check if current user has access to the current tenant based on URL
 */
export const verifyTenantAccess = (): {
  hasAccess: boolean;
  reason?: string;
  redirectUrl?: string;
} => {
  const state = store.getState();
  const { token, isAuthenticated } = state.auth;

  if (!isAuthenticated || !token) {
    return {
      hasAccess: false,
      reason: "Not authenticated",
      redirectUrl: "/auth/login",
    };
  }

  try {
    const decodedToken = jwtDecode<TokenPayload>(token);
    const requestedTenant = getTenantFromUrl();
    const userRole = decodedToken.role;
    const userTenantSlug = decodedToken.tenant_slug;

    // Super admin can access any tenant
    if (userRole === "super_admin") {
      return { hasAccess: true };
    }

    // If no tenant is requested (main domain), check if user can access admin
    if (!requestedTenant) {
      if (userRole === "super_admin" || userRole === "tenant_admin") {
        return { hasAccess: true };
      }
      // Regular tenant users should be redirected to their tenant
      if (userTenantSlug) {
        return {
          hasAccess: false,
          reason: "Tenant users must access through their tenant subdomain",
          redirectUrl: `${window.location.protocol}//${userTenantSlug}.${window.location.host}/dashboard`,
        };
      }
      return {
        hasAccess: false,
        reason: "No tenant access configured",
        redirectUrl: "/auth/login",
      };
    }

    // For tenant-specific URLs, check if user belongs to that tenant
    if (
      userRole === "tenant_admin" ||
      userRole === "tenant_user" ||
      userRole === "tenant_viewer"
    ) {
      if (userTenantSlug === requestedTenant) {
        return { hasAccess: true };
      }

      // User trying to access wrong tenant
      return {
        hasAccess: false,
        reason: `You don't have access to tenant '${requestedTenant}'`,
        redirectUrl: userTenantSlug
          ? `${window.location.protocol}//${userTenantSlug}.${window.location.host}/dashboard`
          : "/auth/login",
      };
    }

    // Default deny
    return {
      hasAccess: false,
      reason: "Access denied",
      redirectUrl: "/auth/login",
    };
  } catch (error) {
    console.error("Error verifying tenant access:", error);
    return {
      hasAccess: false,
      reason: "Invalid token",
      redirectUrl: "/auth/login",
    };
  }
};

/**
 * Get the appropriate login URL based on current context
 */
export const getLoginUrl = (): string => {
  const currentTenant = getTenantFromUrl();

  if (currentTenant) {
    // If we're on a tenant subdomain, keep the login on that subdomain
    return "/auth/login";
  }

  // Main domain login
  return "/auth/login";
};

/**
 * Get the appropriate dashboard URL based on user's role and tenant
 */
export const getDashboardUrl = (): string => {
  const state = store.getState();
  const { token } = state.auth;

  if (!token) {
    return "/dashboard";
  }

  try {
    const decodedToken = jwtDecode<TokenPayload>(token);
    const userRole = decodedToken.role;
    const userTenantSlug = decodedToken.tenant_slug;

    if (userRole === "super_admin") {
      // Super admin goes to admin dashboard
      return "/admin";
    }

    if (userRole === "tenant_admin") {
      // Tenant admin can go to admin or dashboard
      return "/admin";
    }

    if (userTenantSlug) {
      // Regular users go to their tenant dashboard
      const currentHost = window.location.host;
      const currentTenant = getTenantFromUrl();

      // If already on correct tenant subdomain
      if (currentTenant === userTenantSlug) {
        return "/dashboard";
      }

      // Need to redirect to tenant subdomain
      return `${window.location.protocol}//${userTenantSlug}.${currentHost}/dashboard`;
    }

    // Default dashboard
    return "/dashboard";
  } catch (error) {
    console.error("Error getting dashboard URL:", error);
    return "/dashboard";
  }
};

/**
 * Check if user is accessing from correct tenant subdomain
 */
export const isOnCorrectTenantDomain = (): boolean => {
  const state = store.getState();
  const { token } = state.auth;

  if (!token) {
    return false;
  }

  try {
    const decodedToken = jwtDecode<TokenPayload>(token);
    const currentTenant = getTenantFromUrl();
    const userRole = decodedToken.role;
    const userTenantSlug = decodedToken.tenant_slug;

    // Super admin can be on any domain
    if (userRole === "super_admin") {
      return true;
    }

    // If user has no tenant, they should be on main domain
    if (!userTenantSlug) {
      return !currentTenant;
    }

    // User should be on their tenant's subdomain
    return currentTenant === userTenantSlug;
  } catch (error) {
    console.error("Error checking tenant domain:", error);
    return false;
  }
};

/**
 * Format subdomain URL
 */
export const formatSubdomainUrl = (
  tenant: string,
  path: string = "/",
): string => {
  const protocol = window.location.protocol;
  const hostParts = window.location.host.split(".");

  // Remove any existing subdomain
  if (hostParts.length > 2) {
    hostParts.shift();
  }

  const baseHost = hostParts.join(".");
  return `${protocol}//${tenant}.${baseHost}${path}`;
};

/**
 * Remove tenant from URL (go to main domain)
 */
export const getMainDomainUrl = (path: string = "/"): string => {
  const protocol = window.location.protocol;
  const hostParts = window.location.host.split(".");

  // Remove subdomain if present
  if (hostParts.length > 2 && hostParts[0] !== "www") {
    hostParts.shift();
  }

  const baseHost = hostParts.join(".");
  return `${protocol}//${baseHost}${path}`;
};
