import { useState, useCallback } from "react";

export const useTenant = () => {
  const [tenant, setTenant] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadTenantFromUrl = useCallback(() => {
    // Check subdomain
    const hostname = window.location.hostname;
    const parts = hostname.split(".");

    if (parts.length > 2) {
      // Subdomain exists (e.g., tenant1.localhost.com)
      const subdomain = parts[0];
      if (subdomain && subdomain !== "www") {
        setLoading(true);
        // In production, you would fetch tenant details from API
        setTenant({
          id: subdomain,
          name: subdomain,
          slug: subdomain,
        });
        setLoading(false);
        return subdomain;
      }
    }

    // Check path-based tenant (e.g., /t/tenant1)
    const path = window.location.pathname;
    const tenantMatch = path.match(/^\/t\/([^\/]+)/);

    if (tenantMatch) {
      const tenantSlug = tenantMatch[1];
      setLoading(true);
      // In production, you would fetch tenant details from API
      setTenant({
        id: tenantSlug,
        name: tenantSlug,
        slug: tenantSlug,
      });
      setLoading(false);
      return tenantSlug;
    }

    // Check localStorage for saved tenant
    const savedTenant = localStorage.getItem("currentTenant");
    if (savedTenant) {
      try {
        const tenantData = JSON.parse(savedTenant);
        setTenant(tenantData);
        return tenantData.slug;
      } catch (error) {
        console.error("Error parsing saved tenant:", error);
      }
    }

    return null;
  }, []);

  const selectTenant = useCallback((tenantData: any) => {
    setTenant(tenantData);
    localStorage.setItem("currentTenant", JSON.stringify(tenantData));
  }, []);

  const clearTenant = useCallback(() => {
    setTenant(null);
    localStorage.removeItem("currentTenant");
  }, []);

  return {
    tenant,
    loading,
    loadTenantFromUrl,
    selectTenant,
    clearTenant,
  };
};
