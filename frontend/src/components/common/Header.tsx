import React from "react";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../store/store";
import { logout } from "../../store/slices/authSlice";
import { clearTenant } from "../../store/slices/tenantSlice";

const Header: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  const { currentTenant } = useAppSelector((state) => state.tenant);

  const handleLogout = async () => {
    try {
      // Dispatch logout action
      await dispatch(logout()).unwrap();

      // Clear tenant data
      dispatch(clearTenant());

      // Clear all localStorage
      localStorage.clear();

      // Redirect to login
      navigate("/auth/login");
    } catch (error) {
      console.error("Logout error:", error);
      // Even if logout fails on server, clear local state
      localStorage.clear();
      navigate("/auth/login");
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "10px 20px",
        backgroundColor: "#f5f5f5",
        borderBottom: "1px solid #ddd",
        marginBottom: "20px",
      }}
    >
      <div>
        <span style={{ fontWeight: "bold", marginRight: "20px" }}>
          {user?.username || "User"}
        </span>
        {currentTenant && (
          <span style={{ color: "#666" }}>
            @ {currentTenant.name}
          </span>
        )}
      </div>

      <div style={{ display: "flex", gap: "10px" }}>
        <button
          onClick={() => navigate("/dashboard")}
          style={{
            padding: "5px 15px",
            backgroundColor: "#007bff",
            color: "white",
            border: "none",
            borderRadius: "3px",
            cursor: "pointer",
          }}
        >
          Dashboard
        </button>

        <button
          onClick={handleLogout}
          style={{
            padding: "5px 15px",
            backgroundColor: "#dc3545",
            color: "white",
            border: "none",
            borderRadius: "3px",
            cursor: "pointer",
          }}
        >
          Logout
        </button>
      </div>
    </div>
  );
};

export default Header;
