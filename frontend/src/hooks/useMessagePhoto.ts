import { useQuery } from "@tanstack/react-query";

import { getMessagePhotoUrl } from "../api/messages.ts";
import { ApiError } from "../types/api.ts";
import { queryKeys } from "../lib/queryKeys.ts";

export function useMessagePhoto(messageId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.messagePhoto(messageId),
    queryFn: () => getMessagePhotoUrl(messageId),
    enabled,
    staleTime: 60_000,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && (error.status === 502 || (error.status >= 400 && error.status < 500))) {
        return false;
      }
      return failureCount < 1;
    },
  });
}
