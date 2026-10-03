import type { DashboardFilters, DashboardSummary } from "../types/dashboard.ts";
import { apiClient } from "./client.ts";
import { definedParams } from "./params.ts";

export async function getDashboardSummary(filters: DashboardFilters): Promise<DashboardSummary> {
  const response = await apiClient.get<DashboardSummary>("/api/v1/dashboard/summary", {
    params: definedParams({
      date_from: filters.dateFrom,
      date_to: filters.dateTo,
      object_id: filters.objectId ? Number(filters.objectId) : undefined,
    }),
  });
  return response.data;
}
