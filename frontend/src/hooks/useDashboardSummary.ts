import { useQuery } from "@tanstack/react-query";

import { getDashboardSummary } from "../api/dashboard.ts";
import { queryKeys } from "../lib/queryKeys.ts";
import type { DashboardFilters } from "../types/dashboard.ts";

export function useDashboardSummary(filters: DashboardFilters) {
  return useQuery({
    queryKey: queryKeys.dashboard(filters),
    queryFn: () => getDashboardSummary(filters),
  });
}
