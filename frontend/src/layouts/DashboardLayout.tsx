import React from "react";
import { Outlet } from "react-router-dom";
import Header from "../components/common/Header";

const DashboardLayout: React.FC = () => {
  return (
    <div>
      <Header />
      <div style={{ padding: "20px" }}>
        <Outlet />
      </div>
    </div>
  );
};

export default DashboardLayout;
