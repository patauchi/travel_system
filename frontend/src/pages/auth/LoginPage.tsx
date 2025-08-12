import React, { useState, useEffect } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  Divider,
  FormControlLabel,
  Checkbox,
} from "@mui/material";
import {
  Visibility,
  VisibilityOff,
  Person,
  Lock,
  Business,
} from "@mui/icons-material";
import { useAppDispatch, useAppSelector } from "../../store/store";
import { login, clearError } from "../../store/slices/authSlice";
import { fetchTenantBySlug } from "../../store/slices/tenantSlice";
import { getTenantFromSubdomain } from "../../utils/api";

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();

  const { isLoading, error, isAuthenticated } = useAppSelector(
    (state) => state.auth,
  );
  const { currentTenant } = useAppSelector((state) => state.tenant);

  const [formData, setFormData] = useState({
    username: "",
    password: "",
    rememberMe: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<any>({});

  // Get tenant from subdomain
  const tenantSlug = getTenantFromSubdomain();

  // Temporarily disabled to prevent infinite loop
  // useEffect(() => {
  //   // Clear any previous errors
  //   dispatch(clearError());

  //   // If we have a tenant slug from subdomain, fetch tenant info
  //   if (tenantSlug) {
  //     dispatch(fetchTenantBySlug(tenantSlug));
  //   }
  // }, [dispatch, tenantSlug]);

  // Temporarily disabled to prevent infinite loop
  // useEffect(() => {
  //   // Redirect if already authenticated
  //   if (isAuthenticated) {
  //     const from = (location.state as any)?.from?.pathname || "/dashboard";
  //     navigate(from, { replace: true });
  //   }
  // }, [isAuthenticated, navigate, location]);

  const validateForm = () => {
    const errors: any = {};

    if (!formData.username) {
      errors.username = "Username is required";
    } else if (formData.username.length < 3) {
      errors.username = "Username must be at least 3 characters";
    }

    if (!formData.password) {
      errors.password = "Password is required";
    } else if (formData.password.length < 6) {
      errors.password = "Password must be at least 6 characters";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === "rememberMe" ? checked : value,
    }));

    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors((prev: any) => ({
        ...prev,
        [name]: undefined,
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      const result = await dispatch(
        login({
          email: formData.username, // API expects username in the email field
          password: formData.password,
          tenant_slug: tenantSlug || undefined,
        }),
      ).unwrap();

      // If login successful, navigate to dashboard
      if (result) {
        const from = (location.state as any)?.from?.pathname || "/dashboard";
        navigate(from, { replace: true });
      }
    } catch (error: any) {
      console.error("Login failed:", error);
    }
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "background.default",
        py: 4,
      }}
    >
      <Card sx={{ maxWidth: 450, width: "100%", mx: 2 }}>
        <CardContent sx={{ p: 4 }}>
          {/* Logo and Title */}
          <Box sx={{ textAlign: "center", mb: 4 }}>
            {currentTenant ? (
              <>
                <Business sx={{ fontSize: 48, color: "primary.main", mb: 2 }} />
                <Typography variant="h4" component="h1" gutterBottom>
                  {currentTenant.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sign in to your account
                </Typography>
              </>
            ) : (
              <>
                <Typography variant="h4" component="h1" gutterBottom>
                  Welcome Back
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Sign in to continue to your dashboard
                </Typography>
              </>
            )}
          </Box>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Username"
              name="username"
              type="text"
              value={formData.username}
              onChange={handleChange}
              error={!!validationErrors.username}
              helperText={
                validationErrors.username ||
                "Enter your username (e.g., tenant1admin)"
              }
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Person color="action" />
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Password"
              name="password"
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={handleChange}
              error={!!validationErrors.password}
              helperText={validationErrors.password}
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Lock color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleTogglePasswordVisibility}
                      edge="end"
                      disabled={isLoading}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />

            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mb: 3,
              }}
            >
              <FormControlLabel
                control={
                  <Checkbox
                    name="rememberMe"
                    checked={formData.rememberMe}
                    onChange={handleChange}
                    disabled={isLoading}
                  />
                }
                label="Remember me"
              />
              <Link
                to="/auth/forgot-password"
                style={{ textDecoration: "none" }}
              >
                <Typography variant="body2" color="primary">
                  Forgot password?
                </Typography>
              </Link>
            </Box>

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isLoading}
              sx={{ mb: 2 }}
            >
              {isLoading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                "Sign In"
              )}
            </Button>
          </form>

          <Divider sx={{ my: 3 }}>OR</Divider>

          {/* Social Login Buttons (Optional) */}
          <Box sx={{ mb: 3 }}>
            <Button
              fullWidth
              variant="outlined"
              size="large"
              disabled={isLoading}
              sx={{ mb: 1 }}
            >
              Continue with Google
            </Button>
            <Button
              fullWidth
              variant="outlined"
              size="large"
              disabled={isLoading}
            >
              Continue with Microsoft
            </Button>
          </Box>

          {/* Sign Up Link */}
          <Box sx={{ textAlign: "center" }}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account?{" "}
              <Link to="/auth/register" style={{ textDecoration: "none" }}>
                <Typography
                  component="span"
                  variant="body2"
                  color="primary"
                  sx={{ fontWeight: 500 }}
                >
                  Sign up
                </Typography>
              </Link>
            </Typography>
          </Box>

          {/* Return to Landing */}
          {!tenantSlug && (
            <Box sx={{ textAlign: "center", mt: 2 }}>
              <Link to="/" style={{ textDecoration: "none" }}>
                <Typography variant="body2" color="text.secondary">
                  ← Back to home
                </Typography>
              </Link>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default LoginPage;
