#!/bin/bash

# Create stub files for all required components

# Store slices
cat > store/slices/authSlice.ts << 'EOF'
import { createSlice } from '@reduxjs/toolkit';

const authSlice = createSlice({
  name: 'auth',
  initialState: { user: null, isAuthenticated: false },
  reducers: {
    setUser: (state, action) => {
      state.user = action.payload;
      state.isAuthenticated = !!action.payload;
    },
  },
});

export const { setUser } = authSlice.actions;
export default authSlice.reducer;
EOF

cat > store/slices/tenantSlice.ts << 'EOF'
import { createSlice } from '@reduxjs/toolkit';

const tenantSlice = createSlice({
  name: 'tenant',
  initialState: { current: null, list: [] },
  reducers: {
    setCurrentTenant: (state, action) => {
      state.current = action.payload;
    },
  },
});

export const { setCurrentTenant } = tenantSlice.actions;
export default tenantSlice.reducer;
EOF

cat > store/slices/uiSlice.ts << 'EOF'
import { createSlice } from '@reduxjs/toolkit';

const uiSlice = createSlice({
  name: 'ui',
  initialState: { theme: 'light', loading: false },
  reducers: {
    setTheme: (state, action) => {
      state.theme = action.payload;
    },
  },
});

export const { setTheme } = uiSlice.actions;
export default uiSlice.reducer;
EOF

# Layouts
cat > layouts/PublicLayout.tsx << 'EOF'
import React from 'react';
import { Outlet } from 'react-router-dom';

const PublicLayout: React.FC = () => {
  return <div><Outlet /></div>;
};

export default PublicLayout;
EOF

cat > layouts/AuthLayout.tsx << 'EOF'
import React from 'react';
import { Outlet } from 'react-router-dom';

const AuthLayout: React.FC = () => {
  return <div><Outlet /></div>;
};

export default AuthLayout;
EOF

cat > layouts/DashboardLayout.tsx << 'EOF'
import React from 'react';
import { Outlet } from 'react-router-dom';

const DashboardLayout: React.FC = () => {
  return <div><Outlet /></div>;
};

export default DashboardLayout;
EOF

cat > layouts/AdminLayout.tsx << 'EOF'
import React from 'react';
import { Outlet } from 'react-router-dom';

const AdminLayout: React.FC = () => {
  return <div><Outlet /></div>;
};

export default AdminLayout;
EOF

# Public Pages
cat > pages/public/LandingPage.tsx << 'EOF'
import React from 'react';

const LandingPage: React.FC = () => {
  return <div>Landing Page</div>;
};

export default LandingPage;
EOF

cat > pages/public/PricingPage.tsx << 'EOF'
import React from 'react';

const PricingPage: React.FC = () => {
  return <div>Pricing Page</div>;
};

export default PricingPage;
EOF

cat > pages/public/FeaturesPage.tsx << 'EOF'
import React from 'react';

const FeaturesPage: React.FC = () => {
  return <div>Features Page</div>;
};

export default FeaturesPage;
EOF

cat > pages/public/ContactPage.tsx << 'EOF'
import React from 'react';

const ContactPage: React.FC = () => {
  return <div>Contact Page</div>;
};

export default ContactPage;
EOF

# Auth Pages
cat > pages/auth/LoginPage.tsx << 'EOF'
import React from 'react';

const LoginPage: React.FC = () => {
  return <div>Login Page</div>;
};

export default LoginPage;
EOF

cat > pages/auth/RegisterPage.tsx << 'EOF'
import React from 'react';

const RegisterPage: React.FC = () => {
  return <div>Register Page</div>;
};

export default RegisterPage;
EOF

cat > pages/auth/ForgotPasswordPage.tsx << 'EOF'
import React from 'react';

const ForgotPasswordPage: React.FC = () => {
  return <div>Forgot Password Page</div>;
};

export default ForgotPasswordPage;
EOF

cat > pages/auth/ResetPasswordPage.tsx << 'EOF'
import React from 'react';

const ResetPasswordPage: React.FC = () => {
  return <div>Reset Password Page</div>;
};

export default ResetPasswordPage;
EOF

cat > pages/auth/VerifyEmailPage.tsx << 'EOF'
import React from 'react';

const VerifyEmailPage: React.FC = () => {
  return <div>Verify Email Page</div>;
};

export default VerifyEmailPage;
EOF

# Dashboard Pages
cat > pages/dashboard/Dashboard.tsx << 'EOF'
import React from 'react';

const Dashboard: React.FC = () => {
  return <div>Dashboard</div>;
};

export default Dashboard;
EOF

cat > pages/dashboard/Projects.tsx << 'EOF'
import React from 'react';

const Projects: React.FC = () => {
  return <div>Projects</div>;
};

export default Projects;
EOF

cat > pages/dashboard/Documents.tsx << 'EOF'
import React from 'react';

const Documents: React.FC = () => {
  return <div>Documents</div>;
};

export default Documents;
EOF

cat > pages/dashboard/Tasks.tsx << 'EOF'
import React from 'react';

const Tasks: React.FC = () => {
  return <div>Tasks</div>;
};

export default Tasks;
EOF

cat > pages/dashboard/Analytics.tsx << 'EOF'
import React from 'react';

const Analytics: React.FC = () => {
  return <div>Analytics</div>;
};

export default Analytics;
EOF

cat > pages/dashboard/Settings.tsx << 'EOF'
import React from 'react';

const Settings: React.FC = () => {
  return <div>Settings</div>;
};

export default Settings;
EOF

cat > pages/dashboard/Profile.tsx << 'EOF'
import React from 'react';

const Profile: React.FC = () => {
  return <div>Profile</div>;
};

export default Profile;
EOF

cat > pages/dashboard/TeamMembers.tsx << 'EOF'
import React from 'react';

const TeamMembers: React.FC = () => {
  return <div>Team Members</div>;
};

export default TeamMembers;
EOF

# Admin Pages
cat > pages/admin/AdminDashboard.tsx << 'EOF'
import React from 'react';

const AdminDashboard: React.FC = () => {
  return <div>Admin Dashboard</div>;
};

export default AdminDashboard;
EOF

cat > pages/admin/TenantManagement.tsx << 'EOF'
import React from 'react';

const TenantManagement: React.FC = () => {
  return <div>Tenant Management</div>;
};

export default TenantManagement;
EOF

cat > pages/admin/UserManagement.tsx << 'EOF'
import React from 'react';

const UserManagement: React.FC = () => {
  return <div>User Management</div>;
};

export default UserManagement;
EOF

cat > pages/admin/SystemSettings.tsx << 'EOF'
import React from 'react';

const SystemSettings: React.FC = () => {
  return <div>System Settings</div>;
};

export default SystemSettings;
EOF

cat > pages/admin/AuditLogs.tsx << 'EOF'
import React from 'react';

const AuditLogs: React.FC = () => {
  return <div>Audit Logs</div>;
};

export default AuditLogs;
EOF

cat > pages/admin/FeatureFlags.tsx << 'EOF'
import React from 'react';

const FeatureFlags: React.FC = () => {
  return <div>Feature Flags</div>;
};

export default FeatureFlags;
EOF

# Tenant Pages
cat > pages/tenant/TenantSelection.tsx << 'EOF'
import React from 'react';

const TenantSelection: React.FC = () => {
  return <div>Tenant Selection</div>;
};

export default TenantSelection;
EOF

cat > pages/tenant/TenantCreate.tsx << 'EOF'
import React from 'react';

const TenantCreate: React.FC = () => {
  return <div>Create Tenant</div>;
};

export default TenantCreate;
EOF

cat > pages/tenant/TenantSettings.tsx << 'EOF'
import React from 'react';

const TenantSettings: React.FC = () => {
  return <div>Tenant Settings</div>;
};

export default TenantSettings;
EOF

cat > pages/tenant/TenantBilling.tsx << 'EOF'
import React from 'react';

const TenantBilling: React.FC = () => {
  return <div>Tenant Billing</div>;
};

export default TenantBilling;
EOF

# Guards
cat > components/guards/PrivateRoute.tsx << 'EOF'
import React from 'react';
import { Navigate } from 'react-router-dom';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = true; // Mock
  return isAuthenticated ? <>{children}</> : <Navigate to="/auth/login" />;
};

export default PrivateRoute;
EOF

cat > components/guards/TenantRoute.tsx << 'EOF'
import React from 'react';

const TenantRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

export default TenantRoute;
EOF

cat > components/guards/AdminRoute.tsx << 'EOF'
import React from 'react';

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

export default AdminRoute;
EOF

# Hooks
cat > hooks/useAuth.ts << 'EOF'
export const useAuth = () => {
  return {
    user: null,
    login: () => {},
    logout: () => {},
  };
};
EOF

cat > hooks/useTenant.ts << 'EOF'
export const useTenant = () => {
  return {
    tenant: null,
    loadTenantFromUrl: () => {},
  };
};
EOF

cat > hooks/useThemeMode.ts << 'EOF'
export const useThemeMode = () => {
  return {
    themeMode: 'light',
    toggleTheme: () => {},
  };
};
EOF

# Utils
cat > utils/tenant.ts << 'EOF'
export const getTenantFromSubdomain = () => {
  return null;
};
EOF

echo "All stub files created successfully!"
