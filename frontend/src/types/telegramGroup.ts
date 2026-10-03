export type TelegramGroup = {
  id: number;
  telegram_chat_id: number;
  name: string;
  object_id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TelegramGroupWrite = {
  telegram_chat_id: number;
  name: string;
  object_id: number;
  is_active?: boolean;
};

export type TelegramGroupFilters = {
  isActive: "" | "true" | "false";
  objectId: string;
  search: string;
  offset: number;
};
