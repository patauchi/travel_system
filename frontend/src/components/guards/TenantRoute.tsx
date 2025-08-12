import React from "react";
import { Navigate } from "react-router-dom";
import { useAppSelector } from "../../store/store";

const TenantRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { currentTenant } = useAppSelector((state) => state.tenant);

  if (!currentTenant) {
    return <Navigate to="/tenants" replace />;
  }

  return <>{children}</>;
};

export default TenantRoute;
