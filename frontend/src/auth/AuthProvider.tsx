import { useCallback, useEffect, useMemo, useState } from "react";
import { Outlet } from "react-router-dom";

import type { User } from "../types/user.ts";
import { AuthContext } from "./auth-context.ts";
import { subscribeUnauthorized } from "./session.ts";
import { clearAccessToken } from "./tokenStorage.ts";

export function AuthProvider() {
  const [user, setUserState] = useState<User | null>(null);
  const isLoading = false;

  const setUser = useCallback((nextUser: User | null) => {
    setUserState(nextUser);
  }, []);

  const logout = useCallback(() => {
    clearAccessToken();
    setUserState(null);
  }, []);

  useEffect(() => subscribeUnauthorized(() => setUserState(null)), []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      setUser,
      logout,
    }),
    [isLoading, logout, setUser, user],
  );

  return (
    <AuthContext.Provider value={value}>
      <Outlet />
    </AuthContext.Provider>
  );
}
