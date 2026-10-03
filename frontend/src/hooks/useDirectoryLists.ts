import { useQuery } from "@tanstack/react-query";

import { listEmployeePage } from "../api/employees.ts";
import { listWorkObjectPage } from "../api/workObjects.ts";
import { queryKeys } from "../lib/queryKeys.ts";
import type { EmployeeFilters, WorkObjectFilters } from "../types/directory.ts";

export function useEmployeeList(filters: EmployeeFilters) {
  return useQuery({
    queryKey: queryKeys.employeeList(filters),
    queryFn: () => listEmployeePage(filters),
  });
}

export function useWorkObjectList(filters: WorkObjectFilters) {
  return useQuery({
    queryKey: queryKeys.workObjectList(filters),
    queryFn: () => listWorkObjectPage(filters),
  });
}
