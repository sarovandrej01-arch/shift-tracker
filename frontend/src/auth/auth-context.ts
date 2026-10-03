import { createContext } from "react";

import type { User } from "../types/user.ts";

export type AuthContextValue = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
};

export const AuthContext = createContext<AuthContextValue | null>(null);
