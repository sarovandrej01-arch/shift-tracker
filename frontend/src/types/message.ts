import type { Employee } from "./directory.ts";
import type { WorkObject } from "./directory.ts";

export type MessageStatus =
  | "new"
  | "processing"
  | "accepted"
  | "review"
  | "rejected"
  | "duplicate"
  | "error";

export type MessageReason =
  | "no_photo"
  | "employee_not_found"
  | "employee_ambiguous"
  | "group_not_configured"
  | "outside_shift_window"
  | "shift_already_exists"
  | "message_already_processed"
  | "internal_error";

export type Shift = {
  id: number;
  employee_id: number;
  object_id: number;
  shift_date: string;
  source_message_id: number | null;
  confirmed_manually: boolean;
  confirmed_by_user_id: number | null;
  created_at: string;
  updated_at: string;
};

export type ReviewMessage = {
  id: number;
  telegram_message_id: number;
  telegram_chat_id: number;
  telegram_user_id: number | null;
  telegram_username: string | null;
  text: string | null;
  caption: string | null;
  photo_storage_key: string | null;
  telegram_created_at: string;
  employee_id: number | null;
  object_id: number | null;
  shift_date: string | null;
  status: MessageStatus;
  reason: MessageReason | null;
  created_at: string;
  updated_at: string;
};

export type ReviewConfirmRequest = {
  employee_id?: number | null;
  object_id?: number | null;
  shift_date?: string | null;
};

export type ReviewConfirmResponse = {
  message: ReviewMessage;
  shift: Shift;
};

export type ReviewRejectRequest = {
  comment?: string | null;
};

export type ReviewRejectResponse = {
  message: ReviewMessage;
};

export type TelegramMessage = {
  id: number;
  telegram_message_id: number;
  telegram_chat_id: number;
  telegram_user_id: number | null;
  telegram_username: string | null;
  text: string | null;
  caption: string | null;
  photo_file_id: string | null;
  photo_storage_key: string | null;
  telegram_created_at: string;
  edited_at: string | null;
  employee_id: number | null;
  object_id: number | null;
  shift_date: string | null;
  status: MessageStatus;
  reason: MessageReason | null;
  created_at: string;
  updated_at: string;
};

export type MessageDetail = TelegramMessage & {
  employee: Employee | null;
  work_object: WorkObject | null;
  shift: Shift | null;
};

export type MessagePhotoUrl = {
  message_id: number;
  url: string;
  expires_in: number;
};

export type ProcessingLog = {
  id: number;
  message_id: number;
  user_id: number | null;
  action: string;
  details: string | null;
  created_at: string;
};

export type ReviewFilters = {
  reason: string;
  employeeId: string;
  objectId: string;
  dateFrom: string;
  dateTo: string;
  offset: number;
};

export type MessageFilters = {
  status: string;
  reason: string;
  employeeId: string;
  objectId: string;
  dateFrom: string;
  dateTo: string;
  telegramChatId: string;
  telegramUserId: string;
  shiftDateFrom: string;
  shiftDateTo: string;
  offset: number;
};

export const PAGE_SIZE = 20;
