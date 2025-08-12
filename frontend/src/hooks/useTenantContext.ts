import { useState, useEffect } from 'react';

interface TenantContext {
  isTenantContext: boolean;
  tenantSlug: string | null;
  tenantSubdomain: string | null;
  isMainDomain: boolean;
  tenantApiUrl: string;
  authApiUrl: string;
  systemApiUrl: string;
}

export const useTenantContext = (): TenantContext => {
  const [context, setContext] = useState<TenantContext>({
    isTenantContext: false,
    tenantSlug: null,
    tenantSubdomain: null,
    isMainDomain: true,
    tenantApiUrl: '',
    authApiUrl: '',
    systemApiUrl: '',
  });

  useEffect(() => {
    const detectTenantContext = () => {
      const hostname = window.location.hostname;
      const parts = hostname.split('.');

      // Check if we're in a subdomain (e.g., tenant1.localhost or tenant1.example.com)
      const isSubdomain = parts.length >= 2 &&
                         parts[0] !== 'www' &&
                         parts[0] !== 'app' &&
                         parts[0] !== 'api' &&
                         parts[0] !== 'localhost';

      let tenantSlug: string | null = null;
      let tenantSubdomain: string | null = null;

      if (isSubdomain) {
        tenantSubdomain = parts[0];
        tenantSlug = tenantSubdomain;
      }

      // Also check for tenant in path (e.g., /tenant/tenant1)
      const pathParts = window.location.pathname.split('/');
      if (pathParts[1] === 'tenant' && pathParts[2]) {
        tenantSlug = pathParts[2];
        tenantSubdomain = tenantSlug;
      }

      // Determine API URLs based on context
      const baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
      const authServiceUrl = process.env.REACT_APP_AUTH_SERVICE_URL || 'http://localhost:8001';
      const systemServiceUrl = process.env.REACT_APP_SYSTEM_SERVICE_URL || 'http://localhost:8004';

      setContext({
        isTenantContext: !!tenantSlug,
        tenantSlug,
        tenantSubdomain,
        isMainDomain: !tenantSlug,
        tenantApiUrl: tenantSlug ? `${systemServiceUrl}/api/v1/tenants/${tenantSlug}` : '',
        authApiUrl: `${authServiceUrl}/api/v1/auth`,
        systemApiUrl: `${systemServiceUrl}/api/v1`,
      });
    };

    detectTenantContext();

    // Re-detect on navigation changes
    const handleLocationChange = () => detectTenantContext();
    window.addEventListener('popstate', handleLocationChange);

    return () => {
      window.removeEventListener('popstate', handleLocationChange);
    };
  }, []);

  return context;
};

// Helper function to get tenant-aware headers
export const getTenantHeaders = (tenantSlug?: string | null): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const token = localStorage.getItem('access_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (tenantSlug) {
    headers['X-Tenant-Slug'] = tenantSlug;
  }

  return headers;
};

// Helper function to check if user is super admin
export const isSuperAdmin = (): boolean => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return false;

  try {
    const user = JSON.parse(userStr);
    return user.role === 'super_admin';
  } catch {
    return false;
  }
};

// Helper function to check if user is tenant admin
export const isTenantAdmin = (): boolean => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return false;

  try {
    const user = JSON.parse(userStr);
    return user.role === 'admin' || user.role === 'tenant_admin';
  } catch {
    return false;
  }
};

// Helper function to get current user
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;

  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

// Helper function to get current tenant info
export const getCurrentTenant = () => {
  const tenantStr = localStorage.getItem('tenant');
  if (!tenantStr) return null;

  try {
    return JSON.parse(tenantStr);
  } catch {
    return null;
  }
};
