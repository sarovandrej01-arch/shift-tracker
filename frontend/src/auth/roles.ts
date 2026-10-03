import type { User, UserRole } from "../types/user.ts";

export function hasRole(user: User | null, role: UserRole): boolean {
  return user?.role === role;
}

export function canAccessAdmin(user: User | null): boolean {
  return hasRole(user, "admin");
}
