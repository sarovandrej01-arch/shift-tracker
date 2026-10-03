import type { MessageReason, MessageStatus } from "../types/message.ts";

const STATUS_LABELS: Record<MessageStatus, string> = {
  new: "Новое",
  processing: "Обработка",
  accepted: "Принято",
  review: "На проверке",
  rejected: "Отклонено",
  duplicate: "Дубликат",
  error: "Ошибка",
};

const REASON_LABELS: Record<MessageReason, string> = {
  no_photo: "Нет фото",
  employee_not_found: "Сотрудник не найден",
  employee_ambiguous: "Несколько сотрудников",
  group_not_configured: "Группа не настроена",
  outside_shift_window: "Вне окна смены",
  shift_already_exists: "Смена уже существует",
  message_already_processed: "Сообщение уже обработано",
  internal_error: "Внутренняя ошибка",
};

const ACTION_LABELS: Record<string, string> = {
  message_received: "Сообщение получено",
  rejected: "Отклонено",
  processing_error: "Ошибка обработки",
  work_object_resolved: "Объект определён",
  employee_not_found: "Сотрудник не найден",
  employee_ambiguous: "Несколько сотрудников",
  employee_matched: "Сотрудник сопоставлен",
  shift_date_detected: "Дата смены определена",
  duplicate_detected: "Найден дубликат",
  accepted: "Принято",
  review_required: "Отправлено на проверку",
  manual_confirm: "Подтверждено вручную",
  manual_reject: "Отклонено вручную",
};

export function formatMessageStatus(status: MessageStatus): string {
  return STATUS_LABELS[status];
}

export function formatMessageReason(reason: MessageReason | null): string {
  if (!reason) {
    return "—";
  }
  return REASON_LABELS[reason];
}

export function formatProcessingAction(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (dateOnly) {
    return `${dateOnly[3]}.${dateOnly[2]}.${dateOnly[1]}`;
  }
  return formatDateTime(value);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatPeriod(dateFrom: string | null, dateTo: string | null): string {
  if (!dateFrom && !dateTo) {
    return "Период не задан";
  }
  return `${formatDate(dateFrom)} — ${formatDate(dateTo)}`;
}

export function messagePreview(text: string | null, caption: string | null): string {
  const value = caption?.trim() || text?.trim();
  return value || "Без текста";
}

export function formatTelegramUser(username: string | null, userId: number | null): string {
  if (username) {
    return username.startsWith("@") ? username : `@${username}`;
  }
  if (userId !== null) {
    return `ID ${userId}`;
  }
  return "Неизвестный пользователь";
}
