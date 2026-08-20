import { Outlet, useNavigate } from "react-router-dom";
import "./dashboardLayout.css";
import { useAuth } from "@clerk/clerk-react";
import { useEffect, useState } from "react";
import ChatList from "../../components/chatList/chatList";

const DashboardLayout = () => {
  const { userId, isLoaded } = useAuth();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    if (isLoaded && !userId) {
      navigate("/sign-in");
    }
  }, [isLoaded, userId, navigate]);

  if (!isLoaded) {
    return (
      <div className="dashboardLoading">
        <div className="loadingSpinner"></div>
        <span>Initializing workspace...</span>
      </div>
    );
  }

  return (
    <div className={`dashboardLayout ${isSidebarOpen ? "sidebarOpen" : "sidebarCollapsed"}`}>
      <button 
        className="sidebarToggleBtn"
        onClick={() => setIsSidebarOpen(prev => !prev)}
        title={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        aria-label="Toggle sidebar"
      >
        <span className="toggleIcon">{isSidebarOpen ? "‹" : "›"}</span>
      </button>

      <aside className="menu">
        <ChatList />
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
};

export default DashboardLayout;