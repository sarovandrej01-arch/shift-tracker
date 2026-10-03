import { useQuery } from "@tanstack/react-query";

import { listTelegramGroups } from "../api/telegramGroups.ts";
import { listUsers } from "../api/users.ts";
import { queryKeys } from "../lib/queryKeys.ts";
import type { TelegramGroupFilters } from "../types/telegramGroup.ts";
import type { UserFilters } from "../types/user.ts";

export function useUsers(filters: UserFilters) {
  return useQuery({
    queryKey: queryKeys.users(filters),
    queryFn: () => listUsers(filters),
  });
}

export function useTelegramGroups(filters: TelegramGroupFilters) {
  return useQuery({
    queryKey: queryKeys.telegramGroups(filters),
    queryFn: () => listTelegramGroups(filters),
  });
}
