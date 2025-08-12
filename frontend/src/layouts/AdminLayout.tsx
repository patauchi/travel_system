import React from "react";
import { Outlet } from "react-router-dom";
import Header from "../components/common/Header";

const AdminLayout: React.FC = () => {
  return (
    <div>
      <Header />
      <div style={{ padding: "20px" }}>
        <Outlet />
      </div>
    </div>
  );
};

export default AdminLayout;
