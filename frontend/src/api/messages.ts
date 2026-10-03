import type {
  MessageDetail,
  MessageFilters,
  MessagePhotoUrl,
  ProcessingLog,
  TelegramMessage,
} from "../types/message.ts";
import { PAGE_SIZE } from "../types/message.ts";
import { apiClient } from "./client.ts";
import { definedParams } from "./params.ts";

function optionalId(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : undefined;
}

export async function listMessages(filters: MessageFilters): Promise<TelegramMessage[]> {
  const response = await apiClient.get<TelegramMessage[]>("/api/v1/messages", {
    params: definedParams({
      offset: filters.offset,
      limit: PAGE_SIZE,
      status: filters.status,
      reason: filters.reason,
      employee_id: filters.employeeId ? Number(filters.employeeId) : undefined,
      object_id: filters.objectId ? Number(filters.objectId) : undefined,
      date_from: filters.dateFrom,
      date_to: filters.dateTo,
      telegram_chat_id: optionalId(filters.telegramChatId),
      telegram_user_id: optionalId(filters.telegramUserId),
      shift_date_from: filters.shiftDateFrom,
      shift_date_to: filters.shiftDateTo,
    }),
  });
  return response.data;
}

export async function getMessage(messageId: number): Promise<MessageDetail> {
  const response = await apiClient.get<MessageDetail>(`/api/v1/messages/${messageId}`);
  return response.data;
}

export async function getMessagePhotoUrl(messageId: number): Promise<MessagePhotoUrl> {
  const response = await apiClient.get<MessagePhotoUrl>(`/api/v1/messages/${messageId}/photo-url`);
  return response.data;
}

export async function listMessageLogs(messageId: number): Promise<ProcessingLog[]> {
  const response = await apiClient.get<ProcessingLog[]>(`/api/v1/messages/${messageId}/logs`);
  return response.data;
}
