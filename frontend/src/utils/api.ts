import axios, { AxiosInstance, AxiosError } from "axios";
import { store } from "../store/store";

// API Base URLs - Direct service communication for multi-tenant architecture
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const AUTH_SERVICE_URL =
  process.env.REACT_APP_AUTH_SERVICE_URL || "http://localhost:8001";
const TENANT_SERVICE_URL =
  process.env.REACT_APP_TENANT_SERVICE_URL || "http://localhost:8002";
const SYSTEM_SERVICE_URL =
  process.env.REACT_APP_SYSTEM_SERVICE_URL || "http://localhost:8004";
const BUSINESS_SERVICE_URL = API_BASE_URL + "/api/v1/business";

// Helper to detect tenant context
const getTenantContext = () => {
  const hostname = window.location.hostname;
  const parts = hostname.split(".");

  // Check if we're in a subdomain (e.g., tenant1.localhost or tenant1.example.com)
  if (
    parts.length >= 2 &&
    parts[0] !== "www" &&
    parts[0] !== "app" &&
    parts[0] !== "api"
  ) {
    return {
      isTenantContext: true,
      tenantSlug: parts[0],
      tenantSubdomain: parts[0],
    };
  }

  return {
    isTenantContext: false,
    tenantSlug: null,
    tenantSubdomain: null,
  };
};

// Create axios instances for each service
export const apiGateway: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const authService: AxiosInstance = axios.create({
  baseURL: AUTH_SERVICE_URL + "/api/v1/auth",
  headers: {
    "Content-Type": "application/json",
  },
});

export const tenantService: AxiosInstance = axios.create({
  baseURL: TENANT_SERVICE_URL + "/api/v1/tenants",
  headers: {
    "Content-Type": "application/json",
  },
});

export const systemService: AxiosInstance = axios.create({
  baseURL: SYSTEM_SERVICE_URL + "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

export const businessService: AxiosInstance = axios.create({
  baseURL: BUSINESS_SERVICE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
const addAuthInterceptor = (instance: AxiosInstance) => {
  instance.interceptors.request.use(
    (config) => {
      const state = store.getState();
      const token = state.auth?.token;
      const tenantContext = getTenantContext();

      console.log(
        "Request interceptor - Token:",
        token ? "Present" : "Missing",
      );
      console.log("Request URL:", config.url);
      console.log("Request method:", config.method);
      console.log("Tenant context:", tenantContext);

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Add tenant header based on subdomain context
      if (tenantContext.isTenantContext) {
        config.headers["X-Tenant-Slug"] = tenantContext.tenantSlug;
        config.headers["Host"] = window.location.hostname;
      }

      // Add tenant header if we have a current tenant in state
      const currentTenant = state.tenant?.currentTenant;
      if (currentTenant && !tenantContext.isTenantContext) {
        config.headers["X-Tenant-ID"] = currentTenant.id;
        config.headers["X-Tenant-Slug"] = currentTenant.slug;
      }

      console.log("Request headers:", config.headers);
      return config;
    },
    (error) => {
      console.error("Request interceptor error:", error);
      return Promise.reject(error);
    },
  );
};

// Response interceptor to handle errors
const addResponseInterceptor = (instance: AxiosInstance) => {
  instance.interceptors.response.use(
    (response) => {
      console.log("Response received:", response.status, response.config.url);
      return response;
    },
    async (error: AxiosError) => {
      console.error(
        "Response error:",
        error.response?.status,
        error.response?.data,
      );

      if (error.response?.status === 401) {
        // Unauthorized - redirect to login
        console.error("Unauthorized - clearing token");
        localStorage.removeItem("token");
        window.location.href = "/auth/login";
      }

      if (error.response?.status === 403) {
        // Forbidden - user doesn't have permission
        console.error("Permission denied");
      }

      return Promise.reject(error);
    },
  );
};

// Apply interceptors to all instances
[
  apiGateway,
  authService,
  tenantService,
  systemService,
  businessService,
].forEach((instance) => {
  addAuthInterceptor(instance);
  addResponseInterceptor(instance);
});

// Auth API calls
export const authAPI = {
  login: async (credentials: {
    email: string;
    password: string;
    tenant_slug?: string;
  }) => {
    // OAuth2PasswordRequestForm expects form data, not JSON
    const formData = new URLSearchParams();
    formData.append("username", credentials.email); // API expects username, but we use email
    formData.append("password", credentials.password);

    const tenantContext = getTenantContext();
    const headers: any = {
      "Content-Type": "application/x-www-form-urlencoded",
    };

    // Add tenant context to headers if in tenant subdomain
    if (tenantContext.isTenantContext) {
      headers["Host"] = window.location.hostname;
    }

    const response = await authService.post("/login", formData, { headers });

    // Store tenant info if returned
    if (response.data.tenant) {
      localStorage.setItem("tenant", JSON.stringify(response.data.tenant));
    }

    // Store user info
    if (response.data.user) {
      localStorage.setItem("user", JSON.stringify(response.data.user));
    }

    return response.data;
  },

  register: async (data: {
    email: string;
    username: string;
    password: string;
    full_name: string;
    first_name?: string;
    last_name?: string;
  }) => {
    const tenantContext = getTenantContext();
    const headers: any = {
      "Content-Type": "application/json",
    };

    // Add tenant context to headers if in tenant subdomain
    if (tenantContext.isTenantContext) {
      headers["Host"] = window.location.hostname;
    }

    // Split full_name into first_name and last_name if not provided
    if (!data.first_name || !data.last_name) {
      const names = data.full_name.split(" ");
      data.first_name = names[0];
      data.last_name = names.slice(1).join(" ") || "";
    }

    const response = await authService.post("/register", data, { headers });

    // Store tenant info if returned
    if (response.data.tenant) {
      localStorage.setItem("tenant", JSON.stringify(response.data.tenant));
    }

    // Store user info
    if (response.data.user) {
      localStorage.setItem("user", JSON.stringify(response.data.user));
    }

    return response.data;
  },

  logout: async () => {
    const response = await authService.post("/logout");
    return response.data;
  },

  refreshToken: async (refreshToken: string) => {
    const response = await authService.post("/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  forgotPassword: async (email: string) => {
    const response = await authService.post("/forgot-password", { email });
    return response.data;
  },

  resetPassword: async (token: string, newPassword: string) => {
    const response = await authService.post("/reset-password", {
      token,
      new_password: newPassword,
    });
    return response.data;
  },

  verifyEmail: async (token: string) => {
    const response = await authService.post("/verify-email", { token });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await authService.get("/me");
    return response.data;
  },
};

// Tenant API calls
export const tenantAPI = {
  createTenant: async (data: {
    name: string;
    slug: string;
    subdomain: string;
    owner_email: string;
    owner_username: string;
    owner_password: string;
    owner_first_name?: string;
    owner_last_name?: string;
    subscription_plan: string;
  }) => {
    console.log("Creating tenant with data:", data);
    try {
      // Use v2 endpoint for proper multi-tenant architecture
      const response = await tenantService.post("/v2", data);
      console.log("Tenant creation response:", response.data);
      return response.data;
    } catch (error) {
      console.error("Tenant creation error:", error);
      throw error;
    }
  },

  getTenants: async () => {
    const response = await tenantService.get("");
    return response.data;
  },

  getTenant: async (tenantId: string) => {
    const response = await tenantService.get(`/${tenantId}`);
    return response.data;
  },

  updateTenant: async (tenantId: string, data: any) => {
    const response = await tenantService.patch(`/${tenantId}`, data);
    return response.data;
  },

  deleteTenant: async (tenantId: string) => {
    const response = await tenantService.delete(`/${tenantId}`);
    return response.data;
  },

  getTenantBySlug: async (slug: string) => {
    const response = await tenantService.get(`/slug/${slug}`);
    return response.data;
  },

  inviteUserToTenant: async (
    tenantId: string,
    data: {
      email: string;
      role: string;
    },
  ) => {
    const response = await tenantService.post(`/${tenantId}/invite`, data);
    return response.data;
  },

  getTenantUsers: async (tenantId: string) => {
    const response = await tenantService.get(`/${tenantId}/users`);
    return response.data;
  },

  removeTenantUser: async (tenantId: string, userId: string) => {
    const response = await tenantService.delete(`/${tenantId}/users/${userId}`);
    return response.data;
  },

  updateTenantUser: async (
    tenantId: string,
    userId: string,
    data: { role: string },
  ) => {
    const response = await tenantService.patch(
      `/${tenantId}/users/${userId}`,
      data,
    );
    return response.data;
  },
};

// User API calls (within tenant context)
export const userAPI = {
  getUsers: async () => {
    const tenantContext = getTenantContext();

    if (tenantContext.isTenantContext) {
      // Use system service for tenant users
      const response = await systemService.get(
        `/tenants/${tenantContext.tenantSlug}/users`,
      );
      return response.data;
    } else {
      // Use business service for main domain
      const response = await businessService.get("/users");
      return response.data;
    }
  },

  getUser: async (userId: string) => {
    const response = await businessService.get(`/users/${userId}`);
    return response.data;
  },

  createUser: async (data: {
    email: string;
    username: string;
    password: string;
    full_name: string;
    first_name?: string;
    last_name?: string;
    role: string;
  }) => {
    const tenantContext = getTenantContext();

    if (tenantContext.isTenantContext) {
      // Use system service for tenant users
      const response = await systemService.post(
        `/tenants/${tenantContext.tenantSlug}/users`,
        data,
      );
      return response.data;
    } else {
      // Use business service for main domain
      const response = await businessService.post("/users", data);
      return response.data;
    }
  },

  updateUser: async (userId: string, data: any) => {
    const tenantContext = getTenantContext();

    if (tenantContext.isTenantContext) {
      const response = await systemService.patch(
        `/tenants/${tenantContext.tenantSlug}/users/${userId}`,
        data,
      );
      return response.data;
    } else {
      const response = await businessService.patch(`/users/${userId}`, data);
      return response.data;
    }
  },

  deleteUser: async (userId: string) => {
    const tenantContext = getTenantContext();

    if (tenantContext.isTenantContext) {
      const response = await systemService.delete(
        `/tenants/${tenantContext.tenantSlug}/users/${userId}`,
      );
      return response.data;
    } else {
      const response = await businessService.delete(`/users/${userId}`);
      return response.data;
    }
  },

  updateProfile: async (data: any) => {
    const response = await businessService.patch("/users/profile", data);
    return response.data;
  },
};

// Task API calls (within tenant context)
export const taskAPI = {
  getTasks: async (params?: {
    status?: string;
    assigned_to?: string;
    page?: number;
    limit?: number;
  }) => {
    const response = await businessService.get("/tasks", { params });
    return response.data;
  },

  getTask: async (taskId: string) => {
    const response = await businessService.get(`/tasks/${taskId}`);
    return response.data;
  },

  createTask: async (data: {
    title: string;
    description?: string;
    status: string;
    priority: string;
    assigned_to?: string;
    due_date?: string;
  }) => {
    const response = await businessService.post("/tasks", data);
    return response.data;
  },

  updateTask: async (taskId: string, data: any) => {
    const response = await businessService.patch(`/tasks/${taskId}`, data);
    return response.data;
  },

  deleteTask: async (taskId: string) => {
    const response = await businessService.delete(`/tasks/${taskId}`);
    return response.data;
  },

  assignTask: async (taskId: string, userId: string) => {
    const response = await businessService.post(`/tasks/${taskId}/assign`, {
      user_id: userId,
    });
    return response.data;
  },

  updateTaskStatus: async (taskId: string, status: string) => {
    const response = await businessService.patch(`/tasks/${taskId}/status`, {
      status,
    });
    return response.data;
  },
};

// Helper function to get tenant from subdomain
export const getTenantFromSubdomain = (): string | null => {
  const hostname = window.location.hostname;

  // Check if we're on localhost or development
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    // In development, check for subdomain pattern like tenant1.localhost
    const parts = hostname.split(".");
    if (parts.length > 1 && parts[0] !== "www") {
      return parts[0];
    }
  } else {
    // In production, extract subdomain
    const parts = hostname.split(".");
    if (parts.length > 2) {
      return parts[0];
    }
  }

  return null;
};

// Helper function to redirect to tenant subdomain
export const redirectToTenantSubdomain = (slug: string, path: string = "/") => {
  const protocol = window.location.protocol;
  const port = window.location.port ? `:${window.location.port}` : "";

  if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
  ) {
    // In development
    window.location.href = `${protocol}//${slug}.localhost${port}${path}`;
  } else {
    // In production
    const domain = window.location.hostname.split(".").slice(-2).join(".");
    window.location.href = `${protocol}//${slug}.${domain}${port}${path}`;
  }
};

export default {
  authAPI,
  tenantAPI,
  userAPI,
  taskAPI,
  getTenantFromSubdomain,
  redirectToTenantSubdomain,
};
