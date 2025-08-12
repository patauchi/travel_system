import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";
import { authAPI } from "../../utils/api";

interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  tenant_memberships?: any[];
  role?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  userRole: string | null;
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem("token"),
  refreshToken: localStorage.getItem("refreshToken"),
  isAuthenticated: !!localStorage.getItem("token"),
  isLoading: false,
  error: null,
  userRole: null,
};

// Async thunks
export const login = createAsyncThunk(
  "auth/login",
  async (credentials: {
    email: string;
    password: string;
    tenant_slug?: string;
  }) => {
    const response = await authAPI.login(credentials);
    localStorage.setItem("token", response.access_token);
    localStorage.setItem("refreshToken", response.refresh_token);
    return response;
  },
);

export const register = createAsyncThunk(
  "auth/register",
  async (data: {
    email: string;
    username: string;
    password: string;
    full_name: string;
  }) => {
    const response = await authAPI.register(data);
    return response;
  },
);

export const logout = createAsyncThunk("auth/logout", async () => {
  try {
    await authAPI.logout();
  } catch (error) {
    console.error("Logout error:", error);
  }
  localStorage.removeItem("token");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("currentTenant");
});

export const getCurrentUser = createAsyncThunk(
  "auth/getCurrentUser",
  async (_, { getState }) => {
    const state = getState() as { auth: AuthState };
    if (!state.auth.token) {
      throw new Error("No token available");
    }
    const response = await authAPI.getCurrentUser();
    return response;
  },
);

export const refreshToken = createAsyncThunk(
  "auth/refreshToken",
  async (_, { getState }) => {
    const state = getState() as { auth: AuthState };
    const refreshTokenValue = state.auth.refreshToken;
    if (!refreshTokenValue) {
      throw new Error("No refresh token available");
    }
    const response = await authAPI.refreshToken(refreshTokenValue);
    localStorage.setItem("token", response.access_token);
    localStorage.setItem("refreshToken", response.refresh_token);
    return response;
  },
);

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User | null>) => {
      state.user = action.payload;
      state.isAuthenticated = !!action.payload;
      // Extract role from user if available
      if (action.payload?.role) {
        state.userRole = action.payload.role;
      }
    },
    setToken: (state, action: PayloadAction<string | null>) => {
      state.token = action.payload;
      state.isAuthenticated = !!action.payload;
      if (action.payload) {
        localStorage.setItem("token", action.payload);
        // Try to decode token to get role
        try {
          const payload = JSON.parse(atob(action.payload.split(".")[1]));
          state.userRole = payload.role || null;
        } catch (error) {
          console.error("Error decoding token for role:", error);
        }
      } else {
        localStorage.removeItem("token");
        state.userRole = null;
      }
    },
    clearAuth: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.error = null;
      state.userRole = null;
      localStorage.removeItem("token");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("currentTenant");
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.token = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.user = action.payload.user;
        state.error = null;
        // Set user role from response
        if (action.payload.user?.role) {
          state.userRole = action.payload.user.role;
        } else {
          // Try to decode from token if not in user object
          try {
            const payload = JSON.parse(
              atob(action.payload.access_token.split(".")[1]),
            );
            state.userRole = payload.role || null;
          } catch (error) {
            console.error("Error decoding token for role:", error);
          }
        }
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Login failed";
        state.isAuthenticated = false;
      });

    // Register
    builder
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Registration failed";
      });

    // Logout
    builder
      .addCase(logout.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(logout.fulfilled, (state) => {
        state.isLoading = false;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.error = null;
        state.userRole = null;
      })
      .addCase(logout.rejected, (state) => {
        state.isLoading = false;
        // Even if logout fails on server, clear local state
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.userRole = null;
      });

    // Get current user
    builder
      .addCase(getCurrentUser.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
        state.error = null;
        // Set role from user data
        if (action.payload?.role) {
          state.userRole = action.payload.role;
        }
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to get user info";
        // Don't set isAuthenticated to false here if we still have a token
        // This allows retrying the request
        if (!state.token) {
          state.isAuthenticated = false;
        }
      });

    // Refresh token
    builder
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.token = action.payload.access_token;
        state.refreshToken = action.payload.refresh_token;
        state.error = null;
        // Update role from new token
        try {
          const payload = JSON.parse(
            atob(action.payload.access_token.split(".")[1]),
          );
          state.userRole = payload.role || null;
        } catch (error) {
          console.error("Error decoding token for role:", error);
        }
      })
      .addCase(refreshToken.rejected, (state) => {
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.error = "Session expired. Please login again.";
        state.userRole = null;
      });
  },
});

export const { setUser, setToken, clearAuth, clearError } = authSlice.actions;
export default authSlice.reducer;
