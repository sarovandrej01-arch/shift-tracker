import { Navigate } from "react-router-dom";

import { LoadingScreen } from "../components/LoadingScreen.tsx";
import { useAuth } from "../hooks/useAuth.ts";

export function RootRedirect() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />;
}
