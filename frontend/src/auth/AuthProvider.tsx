import { useCallback, useEffect, useMemo, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";

import { getCurrentUser, login as loginRequest } from "../api/auth.ts";
import { ApiError } from "../types/api.ts";
import { normalizeApiError } from "../api/errors.ts";
import { queryClient } from "../lib/queryClient.ts";
import type { LoginRequest } from "../types/auth.ts";
import type { User } from "../types/user.ts";
import { AuthContext } from "./auth-context.ts";
import { subscribeUnauthorized } from "./session.ts";
import { clearAccessToken, getAccessToken, setAccessToken } from "./tokenStorage.ts";

function sessionErrorMessage(error: unknown): string {
  const apiError = error instanceof ApiError ? error : normalizeApiError(error);
  if (apiError.status === 0) {
    return "Не удалось подключиться к серверу";
  }
  return "Не удалось восстановить сессию";
}

export function AuthProvider() {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(() => getAccessToken() !== null);

  const logout = useCallback(() => {
    clearAccessToken();
    setUser(null);
    setAuthError(null);
    queryClient.clear();
    void navigate("/login", { replace: true });
  }, [navigate]);

  const refreshUser = useCallback(async () => {
    const nextUser = await getCurrentUser();
    setUser(nextUser);
    setAuthError(null);
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    setAuthError(null);
    const session = await loginRequest(credentials);
    setAccessToken(session.access_token);
    try {
      const nextUser = await getCurrentUser();
      setUser(nextUser);
    } catch (error) {
      clearAccessToken();
      setUser(null);
      throw error;
    }
  }, []);

  useEffect(() => subscribeUnauthorized(() => setUser(null)), []);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      return;
    }

    let active = true;

    void getCurrentUser()
      .then((nextUser) => {
        if (!active || getAccessToken() !== token) {
          return;
        }
        setUser(nextUser);
        setAuthError(null);
      })
      .catch((error: unknown) => {
        if (!active || getAccessToken() !== token) {
          return;
        }
        const apiError = error instanceof ApiError ? error : normalizeApiError(error);
        setUser(null);
        if (apiError.status === 401) {
          clearAccessToken();
          setAuthError(null);
          return;
        }
        setAuthError(sessionErrorMessage(error));
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      authError,
      login,
      logout,
      refreshUser,
    }),
    [authError, isLoading, login, logout, refreshUser, user],
  );

  return (
    <AuthContext.Provider value={value}>
      <Outlet />
    </AuthContext.Provider>
  );
}
