import type { ShiftDetail, ShiftFilters } from "../types/shift.ts";
import type { Shift } from "../types/message.ts";
import { PAGE_SIZE } from "../types/message.ts";
import { apiClient } from "./client.ts";
import { definedParams } from "./params.ts";

export async function listShifts(filters: ShiftFilters): Promise<Shift[]> {
  const response = await apiClient.get<Shift[]>("/api/v1/shifts", {
    params: definedParams({
      offset: filters.offset,
      limit: PAGE_SIZE,
      employee_id: filters.employeeId ? Number(filters.employeeId) : undefined,
      object_id: filters.objectId ? Number(filters.objectId) : undefined,
      date_from: filters.dateFrom,
      date_to: filters.dateTo,
      confirmed_manually:
        filters.confirmedManually === "" ? undefined : filters.confirmedManually === "true",
    }),
  });
  return response.data;
}

export async function getShiftDetail(shiftId: number): Promise<ShiftDetail> {
  const response = await apiClient.get<ShiftDetail>(`/api/v1/shifts/${shiftId}`);
  return response.data;
}
