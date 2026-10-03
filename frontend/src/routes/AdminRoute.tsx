import { Navigate, Outlet } from "react-router-dom";

import { canAccessAdmin } from "../auth/roles.ts";
import { LoadingScreen } from "../components/LoadingScreen.tsx";
import { useAuth } from "../hooks/useAuth.ts";
import { ForbiddenPage } from "../pages/ForbiddenPage.tsx";

export function AdminRoute() {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!canAccessAdmin(user)) {
    return <ForbiddenPage />;
  }

  return <Outlet />;
}
