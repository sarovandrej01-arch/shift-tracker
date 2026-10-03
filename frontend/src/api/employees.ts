import type { Employee } from "../types/directory.ts";
import { apiClient } from "./client.ts";

export async function listEmployees(): Promise<Employee[]> {
  const response = await apiClient.get<Employee[]>("/api/v1/employees", {
    params: { limit: 100, is_active: true },
  });
  return response.data;
}
