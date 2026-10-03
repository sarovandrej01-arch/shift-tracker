import type { DashboardFilters } from "../types/dashboard.ts";
import type { EmployeeFilters, WorkObjectFilters } from "../types/directory.ts";
import type { MessageFilters, ReviewFilters } from "../types/message.ts";
import type { ShiftFilters } from "../types/shift.ts";

export const queryKeys = {
  dashboard: (filters: DashboardFilters) => ["dashboard", filters] as const,
  reviews: (filters: ReviewFilters) => ["reviews", filters] as const,
  messages: (filters: MessageFilters) => ["messages", filters] as const,
  message: (id: number) => ["message", id] as const,
  messagePhoto: (id: number) => ["message-photo", id] as const,
  messageLogs: (id: number) => ["message-logs", id] as const,
  employees: ["employees"] as const,
  employeeList: (filters: EmployeeFilters) => ["employees", "list", filters] as const,
  workObjects: ["work-objects"] as const,
  workObjectList: (filters: WorkObjectFilters) => ["work-objects", "list", filters] as const,
  shifts: (filters: ShiftFilters) => ["shifts", filters] as const,
  shift: (id: number) => ["shift", id] as const,
};
