import type { WorkObject, WorkObjectFilters, WorkObjectWrite } from "../types/directory.ts";
import { PAGE_SIZE } from "../types/message.ts";
import { apiClient } from "./client.ts";
import { definedParams } from "./params.ts";

type WorkObjectListParams = {
  offset?: number;
  limit?: number;
  isActive?: boolean | null;
  search?: string;
};

export async function listWorkObjects(params: WorkObjectListParams = {}): Promise<WorkObject[]> {
  const isActive = params.isActive === undefined ? true : params.isActive;
  const response = await apiClient.get<WorkObject[]>("/api/v1/work-objects", {
    params: definedParams({
      offset: params.offset ?? 0,
      limit: params.limit ?? 100,
      is_active: isActive === null ? undefined : isActive,
      search: params.search,
    }),
  });
  return response.data;
}

export async function listWorkObjectPage(filters: WorkObjectFilters): Promise<WorkObject[]> {
  return listWorkObjects({
    offset: filters.offset,
    limit: PAGE_SIZE,
    isActive: filters.isActive === "" ? null : filters.isActive === "true",
    search: filters.search,
  });
}

export async function getWorkObject(id: number): Promise<WorkObject> {
  const response = await apiClient.get<WorkObject>(`/api/v1/work-objects/${id}`);
  return response.data;
}

export async function createWorkObject(data: WorkObjectWrite): Promise<WorkObject> {
  const response = await apiClient.post<WorkObject>("/api/v1/work-objects", data);
  return response.data;
}

export async function updateWorkObject(id: number, data: WorkObjectWrite): Promise<WorkObject> {
  const response = await apiClient.patch<WorkObject>(`/api/v1/work-objects/${id}`, {
    name: data.name,
    shift_start_time: data.shift_start_time,
    checkin_before_minutes: data.checkin_before_minutes,
    checkin_after_minutes: data.checkin_after_minutes,
    timezone: data.timezone,
  });
  return response.data;
}

export async function activateWorkObject(id: number): Promise<WorkObject> {
  const response = await apiClient.post<WorkObject>(`/api/v1/work-objects/${id}/activate`);
  return response.data;
}

export async function deactivateWorkObject(id: number): Promise<WorkObject> {
  const response = await apiClient.post<WorkObject>(`/api/v1/work-objects/${id}/deactivate`);
  return response.data;
}
