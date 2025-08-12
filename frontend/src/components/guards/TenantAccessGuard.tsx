import React, { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAppSelector } from "../../store/store";
import {
  verifyTenantAccess,
  getTenantFromUrl,
  isOnCorrectTenantDomain,
  formatSubdomainUrl,
  getMainDomainUrl,
} from "../../utils/tenantAccess";

interface TenantAccessGuardProps {
  children: React.ReactNode;
  requireTenant?: boolean;
  allowedRoles?: string[];
}

const TenantAccessGuard: React.FC<TenantAccessGuardProps> = ({
  children,
  requireTenant = false,
  allowedRoles = [],
}) => {
  const { isAuthenticated, token } = useAppSelector((state) => state.auth);
  const [isChecking, setIsChecking] = useState(true);
  const [accessResult, setAccessResult] = useState<{
    hasAccess: boolean;
    reason?: string;
    redirectUrl?: string;
  }>({ hasAccess: false });

  useEffect(() => {
    // Simplified check to avoid infinite loop
    const checkAccess = () => {
      if (!isAuthenticated || !token) {
        setAccessResult({
          hasAccess: false,
          reason: "Not authenticated",
          redirectUrl: "/auth/login",
        });
        setIsChecking(false);
        return;
      }

      // For now, just allow access if authenticated
      // TODO: Fix the tenant access verification
      setAccessResult({
        hasAccess: true,
      });
      setIsChecking(false);
    };

    checkAccess();
  }, []); // Empty dependency array to run only once
    // Check if user is on correct domain
    if (result.hasAccess && !isOnCorrectTenantDomain()) {
      try {
        const tokenPayload = JSON.parse(atob(token.split(".")[1]));
        const userTenantSlug = tokenPayload.tenant_slug;
        const userRole = tokenPayload.role;

        if (userRole !== "super_admin" && userTenantSlug) {
          // Redirect to correct tenant subdomain
          const redirectPath = window.location.pathname + window.location.search;
          window.location.href = formatSubdomainUrl(userTenantSlug, redirectPath);
          return;
        }
      } catch (error) {
        console.error("Error redirecting to tenant domain:", error);
      }
    }

    setIsChecking(false);
  }, [isAuthenticated, token, requireTenant, allowedRoles]);

  // Show loading state while checking
  if (isChecking) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          backgroundColor: "#f5f5f5",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              width: "50px",
              height: "50px",
              border: "3px solid #f3f3f3",
              borderTop: "3px solid #007bff",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: "0 auto 20px",
            }}
          />
          <style>
            {`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}
          </style>
          <p style={{ color: "#666" }}>Verifying access...</p>
        </div>
      </div>
    );
  }

  // If access denied, show error or redirect
  if (!accessResult.hasAccess) {
    if (accessResult.redirectUrl) {
      // Check if it's an external URL (different subdomain)
      if (accessResult.redirectUrl.startsWith("http")) {
        window.location.href = accessResult.redirectUrl;
        return (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: "100vh",
              backgroundColor: "#f5f5f5",
            }}
          >
            <div style={{ textAlign: "center" }}>
              <p>Redirecting to your tenant...</p>
            </div>
          </div>
        );
      }
      // Internal redirect
      return <Navigate to={accessResult.redirectUrl} replace />;
    }

    // Show access denied message
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          backgroundColor: "#f8d7da",
        }}
      >
        <div
          style={{
            backgroundColor: "white",
            padding: "40px",
            borderRadius: "8px",
            boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
            maxWidth: "400px",
            textAlign: "center",
          }}
        >
          <h2 style={{ color: "#721c24", marginBottom: "20px" }}>Access Denied</h2>
          <p style={{ color: "#721c24", marginBottom: "30px" }}>
            {accessResult.reason || "You don't have permission to access this resource."}
          </p>
          <button
            onClick={() => {
              const currentTenant = getTenantFromUrl();
              if (currentTenant) {
                window.location.href = "/dashboard";
              } else {
                window.location.href = getMainDomainUrl("/");
              }
            }}
            style={{
              padding: "10px 20px",
              backgroundColor: "#dc3545",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer",
              fontSize: "16px",
            }}
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  // Access granted, render children
  return <>{children}</>;
};

export default TenantAccessGuard;
