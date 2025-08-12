import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../store/store";
import { fetchTenants } from "../../store/slices/tenantSlice";
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

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user, token } = useAppSelector((state) => state.auth);
  const { tenants, isLoading } = useAppSelector((state) => state.tenant);
  const [userRole, setUserRole] = useState<string>("tenant_user");
  const [currentTenantInfo, setCurrentTenantInfo] = useState<any>(null);
  const [stats, setStats] = useState({
    totalTenants: 0,
    activeTenants: 0,
    trialTenants: 0,
    totalUsers: 0,
  });

  useEffect(() => {
    // Decode token to get user role and tenant info
    if (token) {
      try {
        const decodedToken = jwtDecode<TokenPayload>(token);
        setUserRole(decodedToken.role);

        // If tenant_admin, get their tenant info
        if (decodedToken.role === "tenant_admin" && decodedToken.tenant_id) {
          // Find the tenant info from the tenants list or make an API call
          const tenantInfo = tenants.find(
            (t) => t.id === decodedToken.tenant_id,
          );
          if (tenantInfo) {
            setCurrentTenantInfo(tenantInfo);
          } else {
            // You might want to fetch the specific tenant info here
            setCurrentTenantInfo({
              id: decodedToken.tenant_id,
              slug: decodedToken.tenant_slug,
              name: `Tenant ${decodedToken.tenant_slug || decodedToken.tenant_id}`,
            });
          }
        }
      } catch (error) {
        console.error("Error decoding token:", error);
      }
    }
  }, [token, tenants]);

  useEffect(() => {
    // Only fetch all tenants if user is super_admin
    if (userRole === "super_admin") {
      dispatch(fetchTenants());
    }
  }, [dispatch, userRole]);

  useEffect(() => {
    // Calculate stats only for super_admin
    if (userRole === "super_admin" && tenants.length > 0) {
      const active = tenants.filter((t: any) => t.status === "active").length;
      const trial = tenants.filter((t: any) => t.status === "trial").length;
      const totalUserCount = tenants.reduce(
        (acc: number, t: any) => acc + (t.user_count || 0),
        0,
      );

      setStats({
        totalTenants: tenants.length,
        activeTenants: active,
        trialTenants: trial,
        totalUsers: totalUserCount,
      });
    }
  }, [tenants, userRole]);

  // Render different content based on user role
  if (userRole === "tenant_admin") {
    return (
      <div style={{ padding: "20px" }}>
        <h1>Admin Dashboard - Tenant Admin</h1>

        <div
          style={{
            backgroundColor: "#f8f9fa",
            padding: "30px",
            borderRadius: "10px",
            marginTop: "20px",
            textAlign: "center",
          }}
        >
          <h2>Hola {currentTenantInfo?.name || "Tenant"}</h2>
          {currentTenantInfo && (
            <div style={{ marginTop: "20px" }}>
              <p>
                <strong>Tenant ID:</strong> {currentTenantInfo.id}
              </p>
              <p>
                <strong>Tenant Slug:</strong> {currentTenantInfo.slug}
              </p>
              {currentTenantInfo.subdomain && (
                <p>
                  <strong>Subdomain:</strong> {currentTenantInfo.subdomain}
                </p>
              )}
            </div>
          )}

          <div style={{ marginTop: "30px" }}>
            <h3>Acciones disponibles para tu tenant:</h3>
            <div
              style={{
                marginTop: "20px",
                display: "flex",
                gap: "10px",
                justifyContent: "center",
                flexWrap: "wrap",
              }}
            >
              <button
                onClick={() => navigate("/dashboard")}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "#007bff",
                  color: "white",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                }}
              >
                Ir al Dashboard del Tenant
              </button>

              <button
                onClick={() => navigate("/admin/users")}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "#28a745",
                  color: "white",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                }}
              >
                Gestionar Usuarios
              </button>

              <button
                onClick={() => navigate("/admin/settings")}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                }}
              >
                Configuración del Tenant
              </button>
            </div>
          </div>
        </div>

        <div style={{ marginTop: "30px" }}>
          <p style={{ color: "#6c757d", fontSize: "14px" }}>
            Como administrador del tenant, puedes gestionar usuarios y
            configuraciones específicas de tu organización.
          </p>
        </div>
      </div>
    );
  }

  // Super Admin View
  if (userRole === "super_admin") {
    return (
      <div style={{ padding: "20px" }}>
        <h1>Super Admin Dashboard</h1>

        {/* Stats Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "20px",
            marginTop: "20px",
          }}
        >
          <div
            style={{
              backgroundColor: "#f8f9fa",
              padding: "20px",
              borderRadius: "8px",
              textAlign: "center",
            }}
          >
            <h3>Total Tenants</h3>
            <p style={{ fontSize: "2em", fontWeight: "bold" }}>
              {stats.totalTenants}
            </p>
          </div>

          <div
            style={{
              backgroundColor: "#d4edda",
              padding: "20px",
              borderRadius: "8px",
              textAlign: "center",
            }}
          >
            <h3>Active Tenants</h3>
            <p
              style={{ fontSize: "2em", fontWeight: "bold", color: "#155724" }}
            >
              {stats.activeTenants}
            </p>
          </div>

          <div
            style={{
              backgroundColor: "#fff3cd",
              padding: "20px",
              borderRadius: "8px",
              textAlign: "center",
            }}
          >
            <h3>Trial Tenants</h3>
            <p
              style={{ fontSize: "2em", fontWeight: "bold", color: "#856404" }}
            >
              {stats.trialTenants}
            </p>
          </div>

          <div
            style={{
              backgroundColor: "#d1ecf1",
              padding: "20px",
              borderRadius: "8px",
              textAlign: "center",
            }}
          >
            <h3>Total Users</h3>
            <p
              style={{ fontSize: "2em", fontWeight: "bold", color: "#0c5460" }}
            >
              {stats.totalUsers}
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{ marginTop: "40px" }}>
          <h2>Quick Actions</h2>
          <div
            style={{
              marginTop: "20px",
              display: "flex",
              gap: "10px",
              flexWrap: "wrap",
            }}
          >
            <button
              onClick={() => navigate("/admin/tenants")}
              style={{
                padding: "10px 20px",
                backgroundColor: "#007bff",
                color: "white",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer",
              }}
            >
              Manage Tenants
            </button>

            <button
              onClick={() => navigate("/admin/users")}
              style={{
                padding: "10px 20px",
                backgroundColor: "#28a745",
                color: "white",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer",
              }}
            >
              Manage Users
            </button>

            <button
              onClick={() => navigate("/admin/settings")}
              style={{
                padding: "10px 20px",
                backgroundColor: "#6c757d",
                color: "white",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer",
              }}
            >
              System Settings
            </button>

            <button
              onClick={() => navigate("/admin/audit-logs")}
              style={{
                padding: "10px 20px",
                backgroundColor: "#17a2b8",
                color: "white",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer",
              }}
            >
              Audit Logs
            </button>

            <button
              onClick={() => navigate("/admin/feature-flags")}
              style={{
                padding: "10px 20px",
                backgroundColor: "#ffc107",
                color: "dark",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer",
              }}
            >
              Feature Flags
            </button>
          </div>
        </div>

        {/* Tenants List */}
        <div style={{ marginTop: "40px" }}>
          <h2>All Tenants</h2>
          {isLoading ? (
            <p>Loading tenants...</p>
          ) : (
            <div
              style={{
                marginTop: "20px",
                backgroundColor: "#fff",
                border: "1px solid #dee2e6",
                borderRadius: "8px",
                overflow: "hidden",
              }}
            >
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ backgroundColor: "#f8f9fa" }}>
                    <th style={{ padding: "12px", textAlign: "left" }}>Name</th>
                    <th style={{ padding: "12px", textAlign: "left" }}>Slug</th>
                    <th style={{ padding: "12px", textAlign: "left" }}>
                      Status
                    </th>
                    <th style={{ padding: "12px", textAlign: "left" }}>Plan</th>
                    <th style={{ padding: "12px", textAlign: "left" }}>
                      Users
                    </th>
                    <th style={{ padding: "12px", textAlign: "left" }}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {tenants.map((tenant: any) => (
                    <tr
                      key={tenant.id}
                      style={{ borderTop: "1px solid #dee2e6" }}
                    >
                      <td style={{ padding: "12px" }}>{tenant.name}</td>
                      <td style={{ padding: "12px" }}>{tenant.slug}</td>
                      <td style={{ padding: "12px" }}>
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "4px",
                            backgroundColor:
                              tenant.status === "active"
                                ? "#d4edda"
                                : "#fff3cd",
                            color:
                              tenant.status === "active"
                                ? "#155724"
                                : "#856404",
                            fontSize: "12px",
                          }}
                        >
                          {tenant.status}
                        </span>
                      </td>
                      <td style={{ padding: "12px" }}>
                        {tenant.subscription_plan}
                      </td>
                      <td style={{ padding: "12px" }}>
                        {tenant.user_count || 0}
                      </td>
                      <td style={{ padding: "12px" }}>
                        <button
                          onClick={() =>
                            navigate(`/admin/tenants/${tenant.id}`)
                          }
                          style={{
                            padding: "5px 10px",
                            backgroundColor: "#007bff",
                            color: "white",
                            border: "none",
                            borderRadius: "3px",
                            cursor: "pointer",
                          }}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                  {tenants.length === 0 && (
                    <tr>
                      <td
                        colSpan={6}
                        style={{ padding: "20px", textAlign: "center" }}
                      >
                        No tenants found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Default view for users without admin privileges (shouldn't happen due to AdminRoute guard)
  return (
    <div style={{ padding: "20px", textAlign: "center" }}>
      <h1>Access Denied</h1>
      <p>You don't have permission to access this area.</p>
      <button
        onClick={() => navigate("/dashboard")}
        style={{
          marginTop: "20px",
          padding: "10px 20px",
          backgroundColor: "#007bff",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
        }}
      >
        Go to Dashboard
      </button>
    </div>
  );
};

export default AdminDashboard;
