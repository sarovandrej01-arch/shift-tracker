export type UserRole = "admin" | "moderator";

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type UserWrite = {
  email: string;
  full_name: string;
  password?: string;
  role: UserRole;
  is_active?: boolean;
};

export type UserFilters = {
  role: "" | UserRole;
  isActive: "" | "true" | "false";
  offset: number;
};
