import React from "react";
import { Navigate } from "react-router-dom";
import { useAppSelector } from "../../store/store";
import { jwtDecode } from "../../utils/jwtHelper";

interface TokenPayload {
  sub: string;
  email: string;
  username: string;
  role: string;
  tenant_id?: string;
  tenant_slug?: string;
  exp: number;
}

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isAuthenticated, token } = useAppSelector(
    (state) => state.auth,
  );

  if (!isAuthenticated || !token) {
    return <Navigate to="/auth/login" replace />;
  }

  try {
    // Decode the token to get the user's role
    const decodedToken = jwtDecode<TokenPayload>(token);

    // Check if user has admin privileges (super_admin or tenant_admin)
    const allowedRoles = ["super_admin", "tenant_admin"];

    if (!allowedRoles.includes(decodedToken.role)) {
      // Redirect non-admin users to their dashboard
      return <Navigate to="/dashboard" replace />;
    }

    // Allow access for admin users
    return <>{children}</>;
  } catch (error) {
    console.error("Error decoding token:", error);
    // If token is invalid, redirect to login
    return <Navigate to="/auth/login" replace />;
  }
};

export default AdminRoute;
