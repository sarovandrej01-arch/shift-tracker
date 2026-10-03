import { createContext } from "react";

import type { LoginRequest } from "../types/auth.ts";
import type { User } from "../types/user.ts";

export type AuthContextValue = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authError: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | null>(null);
