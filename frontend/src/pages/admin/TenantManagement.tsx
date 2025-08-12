import React, { useState, useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../../store/store";
import {
  fetchTenants,
  createTenant,
  deleteTenant,
} from "../../store/slices/tenantSlice";

const TenantManagement: React.FC = () => {
  const dispatch = useAppDispatch();
  const { tenants, isLoading, error } = useAppSelector((state) => state.tenant);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    slug: "",
    subdomain: "",
    owner_email: "",
    owner_username: "",
    owner_password: "",
    owner_first_name: "",
    owner_last_name: "",
    subscription_plan: "starter",
  });

  useEffect(() => {
    console.log("TenantManagement component mounted");
    console.log("Fetching tenants...");
    dispatch(fetchTenants())
      .then(() => console.log("✅ Tenants fetched successfully"))
      .catch((error) => console.error("❌ Failed to fetch tenants:", error));
  }, [dispatch]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    console.log(`Form field changed: ${name} = ${value}`);
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleCreateTenant = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("=== CREATING TENANT V2 ===");
    console.log("Form data:", JSON.stringify(formData, null, 2));
    console.log("Using new multi-tenant architecture");
    console.log("Auth state:", {
      isAuthenticated: localStorage.getItem("token") ? "YES" : "NO",
      token: localStorage.getItem("token") ? "Present" : "Missing",
    });

    setIsCreating(true);

    try {
      console.log("Dispatching createTenant action...");
      const result = await dispatch(createTenant(formData)).unwrap();
      console.log("✅ Tenant created successfully:", result);

      // Clear form
      setShowCreateForm(false);
      setFormData({
        name: "",
        slug: "",
        subdomain: "",
        owner_email: "",
        owner_username: "",
        owner_password: "",
        owner_first_name: "",
        owner_last_name: "",
        subscription_plan: "starter",
      });

      // Refresh tenant list
      console.log("Refreshing tenant list...");
      await dispatch(fetchTenants());
      console.log("✅ Tenant list refreshed");

      alert(
        `✅ Tenant "${result.name}" created successfully!\n\nSlug: ${result.slug}\nSubdomain: ${result.subdomain}`,
      );
    } catch (error: any) {
      console.error("❌ Failed to create tenant:");
      console.error("Error type:", error.name);
      console.error("Error message:", error.message);
      console.error("Error details:", error);

      // Check if it's a network error
      if (error.code === "ERR_NETWORK") {
        alert(
          "Network error: Cannot connect to the backend service. Please check if all services are running.",
        );
      } else if (error.response) {
        // Server responded with error
        const errorMsg =
          error.response.data?.detail ||
          error.response.data?.message ||
          "Unknown server error";
        alert(`Server error: ${errorMsg}`);
      } else {
        alert(`Failed to create tenant: ${error.message || "Unknown error"}`);
      }
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteTenant = async (tenantId: string) => {
    if (window.confirm("Are you sure you want to delete this tenant?")) {
      try {
        await dispatch(deleteTenant(tenantId)).unwrap();
        dispatch(fetchTenants());
      } catch (error) {
        console.error("Failed to delete tenant:", error);
      }
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>Tenant Management</h1>

      <div style={{ marginBottom: "20px" }}>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          style={{
            padding: "10px 20px",
            backgroundColor: "#28a745",
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          {showCreateForm ? "Cancel" : "Create New Tenant"}
        </button>
      </div>

      {showCreateForm && (
        <form
          onSubmit={handleCreateTenant}
          style={{
            border: "1px solid #ccc",
            padding: "20px",
            marginBottom: "20px",
            borderRadius: "5px",
            backgroundColor: "#f9f9f9",
          }}
        >
          <h3>Create New Tenant</h3>
          <div style={{ marginBottom: "10px" }}>
            <label style={{ display: "block", marginBottom: "5px" }}>
              Tenant Name:
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
              style={{ width: "100%", padding: "5px" }}
            />
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label style={{ display: "block", marginBottom: "5px" }}>
              Slug:
            </label>
            <input
              type="text"
              name="slug"
              value={formData.slug}
              onChange={handleInputChange}
              required
              pattern="[a-z0-9-]+"
              style={{ width: "100%", padding: "5px" }}
            />
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label style={{ display: "block", marginBottom: "5px" }}>
              Subdomain:
            </label>
            <input
              type="text"
              name="subdomain"
              value={formData.subdomain}
              onChange={handleInputChange}
              required
              pattern="[a-z0-9-]+"
              style={{ width: "100%", padding: "5px" }}
            />
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label style={{ display: "block", marginBottom: "5px" }}>
              Owner Email:
            </label>
            <input
              type="email"
              name="owner_email"
              value={formData.owner_email}
              onChange={handleInputChange}
              required
              style={{ width: "100%", padding: "5px" }}
            />
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label style={{ display: "block", marginBottom: "5px" }}>
              Owner Username:
            </label>
            <input
              type="text"
              name="owner_username"
              value={formData.owner_username}
              onChange={handleInputChange}
              required
              style={{ width: "100%", padding: "5px" }}
            />
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label style={{ display: "block", marginBottom: "5px" }}>
              Owner Password:
            </label>
            <input
              type="password"
              name="owner_password"
              value={formData.owner_password}
              onChange={handleInputChange}
              required
              minLength={8}
              style={{ width: "100%", padding: "5px" }}
            />
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label style={{ display: "block", marginBottom: "5px" }}>
              Subscription Plan:
            </label>
            <select
              name="subscription_plan"
              value={formData.subscription_plan}
              onChange={handleInputChange}
              style={{ width: "100%", padding: "5px" }}
            >
              <option value="free">Free</option>
              <option value="starter">Starter</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={isCreating}
            style={{
              padding: "10px 20px",
              backgroundColor: isCreating ? "#ccc" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: isCreating ? "not-allowed" : "pointer",
            }}
          >
            {isCreating ? "Creating..." : "Create Tenant"}
          </button>
        </form>
      )}

      {error && (
        <div
          style={{
            padding: "10px",
            backgroundColor: "#f8d7da",
            color: "#721c24",
            border: "1px solid #f5c6cb",
            borderRadius: "5px",
            marginBottom: "20px",
          }}
        >
          Error: {error}
        </div>
      )}

      {isLoading ? (
        <p>Loading tenants...</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "2px solid #ccc" }}>
              <th style={{ padding: "10px", textAlign: "left" }}>Name</th>
              <th style={{ padding: "10px", textAlign: "left" }}>Slug</th>
              <th style={{ padding: "10px", textAlign: "left" }}>Subdomain</th>
              <th style={{ padding: "10px", textAlign: "left" }}>Status</th>
              <th style={{ padding: "10px", textAlign: "left" }}>Plan</th>
              <th style={{ padding: "10px", textAlign: "left" }}>Users</th>
              <th style={{ padding: "10px", textAlign: "left" }}>Storage</th>
              <th style={{ padding: "10px", textAlign: "left" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((tenant) => (
              <tr key={tenant.id} style={{ borderBottom: "1px solid #eee" }}>
                <td style={{ padding: "10px" }}>{tenant.name}</td>
                <td style={{ padding: "10px" }}>{tenant.slug}</td>
                <td style={{ padding: "10px" }}>{tenant.subdomain}</td>
                <td style={{ padding: "10px" }}>
                  <span
                    style={{
                      padding: "2px 8px",
                      borderRadius: "3px",
                      backgroundColor:
                        tenant.status === "active"
                          ? "#d4edda"
                          : tenant.status === "trial"
                            ? "#fff3cd"
                            : "#f8d7da",
                      color:
                        tenant.status === "active"
                          ? "#155724"
                          : tenant.status === "trial"
                            ? "#856404"
                            : "#721c24",
                    }}
                  >
                    {tenant.status}
                  </span>
                </td>
                <td style={{ padding: "10px" }}>{tenant.subscription_plan}</td>
                <td style={{ padding: "10px" }}>
                  {tenant.user_count}/{tenant.max_users}
                </td>
                <td style={{ padding: "10px" }}>
                  {tenant.storage_used_gb}/{tenant.max_storage_gb} GB
                </td>
                <td style={{ padding: "10px" }}>
                  <button
                    onClick={() => handleDeleteTenant(tenant.id)}
                    style={{
                      padding: "5px 10px",
                      backgroundColor: "#dc3545",
                      color: "white",
                      border: "none",
                      borderRadius: "3px",
                      cursor: "pointer",
                      marginRight: "5px",
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default TenantManagement;
