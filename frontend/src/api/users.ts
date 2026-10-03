import type { User, UserFilters, UserWrite } from "../types/user.ts";
import { PAGE_SIZE } from "../types/message.ts";
import { apiClient } from "./client.ts";
import { definedParams } from "./params.ts";

export async function listUsers(filters: UserFilters): Promise<User[]> {
  const response = await apiClient.get<User[]>("/api/v1/users", {
    params: definedParams({
      offset: filters.offset,
      limit: PAGE_SIZE,
      role: filters.role,
      is_active: filters.isActive === "" ? undefined : filters.isActive === "true",
    }),
  });
  return response.data;
}

export async function getUser(id: number): Promise<User> {
  const response = await apiClient.get<User>(`/api/v1/users/${id}`);
  return response.data;
}

export async function createUser(data: UserWrite): Promise<User> {
  const response = await apiClient.post<User>("/api/v1/users", data);
  return response.data;
}

export async function updateUser(id: number, data: UserWrite): Promise<User> {
  const body: { email: string; full_name: string; role: UserWrite["role"]; password?: string } = {
    email: data.email,
    full_name: data.full_name,
    role: data.role,
  };
  if (data.password) {
    body.password = data.password;
  }
  const response = await apiClient.patch<User>(`/api/v1/users/${id}`, body);
  return response.data;
}

export async function activateUser(id: number): Promise<User> {
  const response = await apiClient.post<User>(`/api/v1/users/${id}/activate`);
  return response.data;
}

export async function deactivateUser(id: number): Promise<User> {
  const response = await apiClient.post<User>(`/api/v1/users/${id}/deactivate`);
  return response.data;
}
