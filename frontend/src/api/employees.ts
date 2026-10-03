import type { Employee, EmployeeFilters, EmployeeWrite } from "../types/directory.ts";
import { PAGE_SIZE } from "../types/message.ts";
import { apiClient } from "./client.ts";
import { definedParams } from "./params.ts";

type EmployeeListParams = {
  offset?: number;
  limit?: number;
  isActive?: boolean | null;
  search?: string;
};

export async function listEmployees(params: EmployeeListParams = {}): Promise<Employee[]> {
  const isActive = params.isActive === undefined ? true : params.isActive;
  const response = await apiClient.get<Employee[]>("/api/v1/employees", {
    params: definedParams({
      offset: params.offset ?? 0,
      limit: params.limit ?? 100,
      is_active: isActive === null ? undefined : isActive,
      search: params.search,
    }),
  });
  return response.data;
}

export async function listEmployeePage(filters: EmployeeFilters): Promise<Employee[]> {
  return listEmployees({
    offset: filters.offset,
    limit: PAGE_SIZE,
    isActive: filters.isActive === "" ? null : filters.isActive === "true",
    search: filters.search,
  });
}

export async function getEmployee(id: number): Promise<Employee> {
  const response = await apiClient.get<Employee>(`/api/v1/employees/${id}`);
  return response.data;
}

export async function createEmployee(data: EmployeeWrite): Promise<Employee> {
  const response = await apiClient.post<Employee>("/api/v1/employees", data);
  return response.data;
}

export async function updateEmployee(id: number, data: EmployeeWrite): Promise<Employee> {
  const response = await apiClient.patch<Employee>(`/api/v1/employees/${id}`, {
    full_name: data.full_name,
    personnel_number: data.personnel_number,
    telegram_user_id: data.telegram_user_id,
    telegram_username: data.telegram_username,
    callsign: data.callsign,
  });
  return response.data;
}

export async function activateEmployee(id: number): Promise<Employee> {
  const response = await apiClient.post<Employee>(`/api/v1/employees/${id}/activate`);
  return response.data;
}

export async function deactivateEmployee(id: number): Promise<Employee> {
  const response = await apiClient.post<Employee>(`/api/v1/employees/${id}/deactivate`);
  return response.data;
}
