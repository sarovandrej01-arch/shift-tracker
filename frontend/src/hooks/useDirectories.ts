import { useQuery } from "@tanstack/react-query";

import { listEmployees } from "../api/employees.ts";
import { listWorkObjects } from "../api/workObjects.ts";
import { queryKeys } from "../lib/queryKeys.ts";

export function useEmployees() {
  return useQuery({
    queryKey: queryKeys.employees,
    queryFn: listEmployees,
  });
}

export function useWorkObjects() {
  return useQuery({
    queryKey: queryKeys.workObjects,
    queryFn: listWorkObjects,
  });
}
