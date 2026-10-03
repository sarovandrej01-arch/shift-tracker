import { useQuery } from "@tanstack/react-query";

import { getMessage, listMessageLogs, listMessages } from "../api/messages.ts";
import { queryKeys } from "../lib/queryKeys.ts";
import type { MessageFilters } from "../types/message.ts";

export function useMessages(filters: MessageFilters) {
  return useQuery({
    queryKey: queryKeys.messages(filters),
    queryFn: () => listMessages(filters),
  });
}

export function useMessageDetail(messageId: number | null) {
  return useQuery({
    queryKey: queryKeys.message(messageId ?? 0),
    queryFn: () => getMessage(messageId ?? 0),
    enabled: messageId !== null,
  });
}

export function useMessageLogs(messageId: number | null) {
  return useQuery({
    queryKey: queryKeys.messageLogs(messageId ?? 0),
    queryFn: () => listMessageLogs(messageId ?? 0),
    enabled: messageId !== null,
  });
}
