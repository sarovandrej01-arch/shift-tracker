import { Navigate, Outlet } from "react-router-dom";

import { LoadingScreen } from "../components/LoadingScreen.tsx";
import { useAuth } from "../hooks/useAuth.ts";

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
