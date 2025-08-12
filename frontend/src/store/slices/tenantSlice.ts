import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";
import { tenantAPI } from "../../utils/api";

interface Tenant {
  id: string;
  name: string;
  slug: string;
  subdomain: string;
  domain?: string;
  status: string;
  subscription_plan: string;
  max_users: number;
  max_storage_gb: number;
  created_at: string;
  trial_ends_at?: string;
  user_count: number;
  storage_used_gb: number;
}

interface TenantUser {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface TenantState {
  currentTenant: Tenant | null;
  tenants: Tenant[];
  tenantUsers: TenantUser[];
  isLoading: boolean;
  error: string | null;
}

const storedTenant = localStorage.getItem("currentTenant");
const initialState: TenantState = {
  currentTenant: storedTenant ? JSON.parse(storedTenant) : null,
  tenants: [],
  tenantUsers: [],
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchTenants = createAsyncThunk(
  "tenant/fetchTenants",
  async () => {
    const response = await tenantAPI.getTenants();
    return response;
  },
);

export const fetchTenant = createAsyncThunk(
  "tenant/fetchTenant",
  async (tenantId: string) => {
    const response = await tenantAPI.getTenant(tenantId);
    return response;
  },
);

export const fetchTenantBySlug = createAsyncThunk(
  "tenant/fetchTenantBySlug",
  async (slug: string) => {
    const response = await tenantAPI.getTenantBySlug(slug);
    return response;
  },
);

export const createTenant = createAsyncThunk(
  "tenant/createTenant",
  async (data: {
    name: string;
    slug: string;
    subdomain: string;
    owner_email: string;
    owner_username: string;
    owner_password: string;
    subscription_plan: string;
  }) => {
    const response = await tenantAPI.createTenant(data);
    return response;
  },
);

export const updateTenant = createAsyncThunk(
  "tenant/updateTenant",
  async ({ tenantId, data }: { tenantId: string; data: any }) => {
    const response = await tenantAPI.updateTenant(tenantId, data);
    return response;
  },
);

export const deleteTenant = createAsyncThunk(
  "tenant/deleteTenant",
  async (tenantId: string) => {
    await tenantAPI.deleteTenant(tenantId);
    return tenantId;
  },
);

export const fetchTenantUsers = createAsyncThunk(
  "tenant/fetchTenantUsers",
  async (tenantId: string) => {
    const response = await tenantAPI.getTenantUsers(tenantId);
    return response;
  },
);

export const inviteUserToTenant = createAsyncThunk(
  "tenant/inviteUser",
  async ({
    tenantId,
    data,
  }: {
    tenantId: string;
    data: { email: string; role: string };
  }) => {
    const response = await tenantAPI.inviteUserToTenant(tenantId, data);
    return response;
  },
);

export const removeTenantUser = createAsyncThunk(
  "tenant/removeUser",
  async ({ tenantId, userId }: { tenantId: string; userId: string }) => {
    await tenantAPI.removeTenantUser(tenantId, userId);
    return userId;
  },
);

export const updateTenantUser = createAsyncThunk(
  "tenant/updateUser",
  async ({
    tenantId,
    userId,
    data,
  }: {
    tenantId: string;
    userId: string;
    data: { role: string };
  }) => {
    const response = await tenantAPI.updateTenantUser(tenantId, userId, data);
    return response;
  },
);

const tenantSlice = createSlice({
  name: "tenant",
  initialState,
  reducers: {
    setCurrentTenant: (state, action: PayloadAction<Tenant | null>) => {
      state.currentTenant = action.payload;
      if (action.payload) {
        localStorage.setItem("currentTenant", JSON.stringify(action.payload));
      } else {
        localStorage.removeItem("currentTenant");
      }
    },
    clearTenant: (state) => {
      state.currentTenant = null;
      state.tenants = [];
      state.tenantUsers = [];
      state.error = null;
      localStorage.removeItem("currentTenant");
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch tenants
    builder
      .addCase(fetchTenants.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTenants.fulfilled, (state, action) => {
        state.isLoading = false;
        state.tenants = action.payload;
        state.error = null;
      })
      .addCase(fetchTenants.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to fetch tenants";
      });

    // Fetch single tenant
    builder
      .addCase(fetchTenant.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTenant.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentTenant = action.payload;
        localStorage.setItem("currentTenant", JSON.stringify(action.payload));
        state.error = null;
      })
      .addCase(fetchTenant.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to fetch tenant";
      });

    // Fetch tenant by slug
    builder
      .addCase(fetchTenantBySlug.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTenantBySlug.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentTenant = action.payload;
        localStorage.setItem("currentTenant", JSON.stringify(action.payload));
        state.error = null;
      })
      .addCase(fetchTenantBySlug.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to fetch tenant";
      });

    // Create tenant
    builder
      .addCase(createTenant.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createTenant.fulfilled, (state, action) => {
        state.isLoading = false;
        state.tenants.push(action.payload);
        state.error = null;
      })
      .addCase(createTenant.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to create tenant";
      });

    // Update tenant
    builder
      .addCase(updateTenant.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateTenant.fulfilled, (state, action) => {
        state.isLoading = false;
        const index = state.tenants.findIndex(
          (t) => t.id === action.payload.id,
        );
        if (index !== -1) {
          state.tenants[index] = action.payload;
        }
        if (state.currentTenant?.id === action.payload.id) {
          state.currentTenant = action.payload;
          localStorage.setItem("currentTenant", JSON.stringify(action.payload));
        }
        state.error = null;
      })
      .addCase(updateTenant.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to update tenant";
      });

    // Delete tenant
    builder
      .addCase(deleteTenant.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(deleteTenant.fulfilled, (state, action) => {
        state.isLoading = false;
        state.tenants = state.tenants.filter((t) => t.id !== action.payload);
        if (state.currentTenant?.id === action.payload) {
          state.currentTenant = null;
          localStorage.removeItem("currentTenant");
        }
        state.error = null;
      })
      .addCase(deleteTenant.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to delete tenant";
      });

    // Fetch tenant users
    builder
      .addCase(fetchTenantUsers.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTenantUsers.fulfilled, (state, action) => {
        state.isLoading = false;
        state.tenantUsers = action.payload;
        state.error = null;
      })
      .addCase(fetchTenantUsers.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to fetch tenant users";
      });

    // Invite user to tenant
    builder
      .addCase(inviteUserToTenant.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(inviteUserToTenant.fulfilled, (state, action) => {
        state.isLoading = false;
        state.tenantUsers.push(action.payload);
        state.error = null;
      })
      .addCase(inviteUserToTenant.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to invite user";
      });

    // Remove tenant user
    builder
      .addCase(removeTenantUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(removeTenantUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.tenantUsers = state.tenantUsers.filter(
          (u) => u.id !== action.payload,
        );
        state.error = null;
      })
      .addCase(removeTenantUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to remove user";
      });

    // Update tenant user
    builder
      .addCase(updateTenantUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateTenantUser.fulfilled, (state, action) => {
        state.isLoading = false;
        const index = state.tenantUsers.findIndex(
          (u) => u.id === action.payload.id,
        );
        if (index !== -1) {
          state.tenantUsers[index] = action.payload;
        }
        state.error = null;
      })
      .addCase(updateTenantUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to update user";
      });
  },
});

export const { setCurrentTenant, clearTenant, clearError } =
  tenantSlice.actions;
export default tenantSlice.reducer;
