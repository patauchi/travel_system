import React, { useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { CssBaseline, Box } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Provider, useDispatch } from "react-redux";
import { store, useAppDispatch } from "./store/store";
import { setUser, setToken, getCurrentUser } from "./store/slices/authSlice";
import { setCurrentTenant } from "./store/slices/tenantSlice";

// Layout Components
import PublicLayout from "./layouts/PublicLayout";
import AuthLayout from "./layouts/AuthLayout";
import DashboardLayout from "./layouts/DashboardLayout";
import AdminLayout from "./layouts/AdminLayout";

// Public Pages
import LandingPage from "./pages/public/LandingPage";
import PricingPage from "./pages/public/PricingPage";
import FeaturesPage from "./pages/public/FeaturesPage";
import ContactPage from "./pages/public/ContactPage";

// Auth Pages
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import ForgotPasswordPage from "./pages/auth/ForgotPasswordPage";
import ResetPasswordPage from "./pages/auth/ResetPasswordPage";
import VerifyEmailPage from "./pages/auth/VerifyEmailPage";

// Dashboard Pages
import Dashboard from "./pages/dashboard/Dashboard";
import Projects from "./pages/dashboard/Projects";
import Documents from "./pages/dashboard/Documents";
import Tasks from "./pages/dashboard/Tasks";
import Analytics from "./pages/dashboard/Analytics";
import Settings from "./pages/dashboard/Settings";
import Profile from "./pages/dashboard/Profile";
import TeamMembers from "./pages/dashboard/TeamMembers";

// Admin Pages
import AdminDashboard from "./pages/admin/AdminDashboard";
import TenantManagement from "./pages/admin/TenantManagement";
import UserManagement from "./pages/admin/UserManagement";
import SystemSettings from "./pages/admin/SystemSettings";
import AuditLogs from "./pages/admin/AuditLogs";
import FeatureFlags from "./pages/admin/FeatureFlags";

// Tenant Pages
import TenantSelection from "./pages/tenant/TenantSelection";
import TenantCreate from "./pages/tenant/TenantCreate";
import TenantSettings from "./pages/tenant/TenantSettings";
import TenantBilling from "./pages/tenant/TenantBilling";

// Guards and Utilities
import PrivateRoute from "./components/guards/PrivateRoute";
import TenantRoute from "./components/guards/TenantRoute";
import AdminRoute from "./components/guards/AdminRoute";
import TenantAccessGuard from "./components/guards/TenantAccessGuard";

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// Create theme
const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1976d2",
      light: "#42a5f5",
      dark: "#1565c0",
    },
    secondary: {
      main: "#dc004e",
      light: "#e33371",
      dark: "#9a0036",
    },
    background: {
      default: "#f5f5f5",
      paper: "#ffffff",
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: "2.5rem",
      fontWeight: 600,
    },
    h2: {
      fontSize: "2rem",
      fontWeight: 600,
    },
    h3: {
      fontSize: "1.75rem",
      fontWeight: 600,
    },
    h4: {
      fontSize: "1.5rem",
      fontWeight: 500,
    },
    h5: {
      fontSize: "1.25rem",
      fontWeight: 500,
    },
    h6: {
      fontSize: "1rem",
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: "0px 2px 4px rgba(0, 0, 0, 0.1)",
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        variant: "outlined",
        fullWidth: true,
      },
    },
  },
});

function AppRoutes() {
  const dispatch = useAppDispatch();

  useEffect(() => {
    // Initialize auth state from localStorage
    const token = localStorage.getItem("token");
    const refreshToken = localStorage.getItem("refreshToken");
    const currentTenant = localStorage.getItem("currentTenant");

    if (token) {
      // Set token in state
      dispatch(setToken(token));

      // Temporarily disabled to avoid infinite loop
      // TODO: Fix getCurrentUser to not cause re-renders
      // dispatch(getCurrentUser()).catch((error) => {
      //   console.error("Failed to get user info:", error);
      //   // If getting user info fails, clear the invalid token
      //   localStorage.removeItem("token");
      //   localStorage.removeItem("refreshToken");
      // });
    }

    if (currentTenant) {
      try {
        const tenant = JSON.parse(currentTenant);
        dispatch(setCurrentTenant(tenant));
      } catch (error) {
        console.error("Failed to parse tenant info:", error);
        localStorage.removeItem("currentTenant");
      }
    }
  }, []); // Remove dispatch from dependencies to prevent re-runs

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<PublicLayout />}>
        <Route index element={<LandingPage />} />
        <Route path="pricing" element={<PricingPage />} />
        <Route path="features" element={<FeaturesPage />} />
        <Route path="contact" element={<ContactPage />} />
      </Route>

      {/* Auth Routes */}
      <Route path="/auth" element={<AuthLayout />}>
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="forgot-password" element={<ForgotPasswordPage />} />
        <Route path="reset-password" element={<ResetPasswordPage />} />
        <Route path="verify-email" element={<VerifyEmailPage />} />
      </Route>

      {/* Tenant Selection (for users with multiple tenants) */}
      <Route
        path="/tenants"
        element={
          <PrivateRoute>
            <PublicLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<TenantSelection />} />
        <Route path="create" element={<TenantCreate />} />
      </Route>

      {/* Dashboard Routes (Tenant-specific) */}
      {/* Protected Routes - Dashboard */}
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <TenantAccessGuard>
              <DashboardLayout />
            </TenantAccessGuard>
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="documents" element={<Documents />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="team" element={<TeamMembers />} />
        <Route path="settings" element={<Settings />} />
        <Route path="profile" element={<Profile />} />

        {/* Tenant Admin Routes */}
        <Route path="tenant">
          <Route path="settings" element={<TenantSettings />} />
          <Route path="billing" element={<TenantBilling />} />
        </Route>
      </Route>

      {/* Super Admin Routes */}
      <Route
        path="/admin"
        element={
          <PrivateRoute>
            <AdminRoute>
              <TenantAccessGuard allowedRoles={["super_admin", "tenant_admin"]}>
                <AdminLayout />
              </TenantAccessGuard>
            </AdminRoute>
          </PrivateRoute>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="tenants" element={<TenantManagement />} />
        <Route path="users" element={<UserManagement />} />
        <Route path="settings" element={<SystemSettings />} />
        <Route path="audit-logs" element={<AuditLogs />} />
        <Route path="feature-flags" element={<FeatureFlags />} />
      </Route>

      {/* Catch all - 404 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Router>
            <AppRoutes />
          </Router>
        </ThemeProvider>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
