import { useQuery } from "@tanstack/react-query";

import { getShiftDetail, listShifts } from "../api/shifts.ts";
import { queryKeys } from "../lib/queryKeys.ts";
import type { ShiftFilters } from "../types/shift.ts";

export function useShifts(filters: ShiftFilters) {
  return useQuery({
    queryKey: queryKeys.shifts(filters),
    queryFn: () => listShifts(filters),
  });
}

export function useShiftDetail(shiftId: number | null) {
  return useQuery({
    queryKey: queryKeys.shift(shiftId ?? 0),
    queryFn: () => getShiftDetail(shiftId ?? 0),
    enabled: shiftId !== null,
  });
}
