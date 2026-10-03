import type { WorkObject } from "../types/directory.ts";
import { apiClient } from "./client.ts";

export async function listWorkObjects(): Promise<WorkObject[]> {
  const response = await apiClient.get<WorkObject[]>("/api/v1/work-objects", {
    params: { limit: 100, is_active: true },
  });
  return response.data;
}
