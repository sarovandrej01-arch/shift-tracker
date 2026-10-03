import type { TelegramGroup, TelegramGroupFilters, TelegramGroupWrite } from "../types/telegramGroup.ts";
import { PAGE_SIZE } from "../types/message.ts";
import { apiClient } from "./client.ts";
import { definedParams } from "./params.ts";

export async function listTelegramGroups(filters: TelegramGroupFilters): Promise<TelegramGroup[]> {
  const response = await apiClient.get<TelegramGroup[]>("/api/v1/telegram-groups", {
    params: definedParams({
      offset: filters.offset,
      limit: PAGE_SIZE,
      is_active: filters.isActive === "" ? undefined : filters.isActive === "true",
      object_id: filters.objectId ? Number(filters.objectId) : undefined,
      search: filters.search,
    }),
  });
  return response.data;
}

export async function getTelegramGroup(id: number): Promise<TelegramGroup> {
  const response = await apiClient.get<TelegramGroup>(`/api/v1/telegram-groups/${id}`);
  return response.data;
}

export async function createTelegramGroup(data: TelegramGroupWrite): Promise<TelegramGroup> {
  const response = await apiClient.post<TelegramGroup>("/api/v1/telegram-groups", data);
  return response.data;
}

export async function updateTelegramGroup(id: number, data: TelegramGroupWrite): Promise<TelegramGroup> {
  const response = await apiClient.patch<TelegramGroup>(`/api/v1/telegram-groups/${id}`, {
    telegram_chat_id: data.telegram_chat_id,
    name: data.name,
    object_id: data.object_id,
  });
  return response.data;
}

export async function activateTelegramGroup(id: number): Promise<TelegramGroup> {
  const response = await apiClient.post<TelegramGroup>(`/api/v1/telegram-groups/${id}/activate`);
  return response.data;
}

export async function deactivateTelegramGroup(id: number): Promise<TelegramGroup> {
  const response = await apiClient.post<TelegramGroup>(`/api/v1/telegram-groups/${id}/deactivate`);
  return response.data;
}
