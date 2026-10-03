import { ApiError } from "../types/api.ts";
import { normalizeApiError } from "../api/errors.ts";

export function getApiErrorMessage(error: unknown): string {
  const apiError = error instanceof ApiError ? error : normalizeApiError(error);

  if (apiError.status === 401) {
    return "Сессия истекла";
  }
  if (apiError.status === 403) {
    return "Недостаточно прав";
  }
  if (apiError.status === 404) {
    return "Не найдено";
  }
  if (apiError.status === 409) {
    if (apiError.detail === "Shift already exists") {
      return "Смена на эту дату уже существует";
    }
    if (apiError.detail === "Employee with this personnel number already exists") {
      return "Сотрудник с таким табельным номером уже есть";
    }
    if (apiError.detail === "Employee with this Telegram user ID already exists") {
      return "Сотрудник с таким Telegram ID уже есть";
    }
    if (apiError.detail === "Work object with this name already exists") {
      return "Объект с таким названием уже есть";
    }
    return "Сообщение уже было обработано";
  }
  if (apiError.status === 422) {
    if (apiError.detail?.includes("date_from")) {
      return "Дата начала не может быть позже даты окончания";
    }
    return "Проверьте введённые данные";
  }
  if (apiError.status === 502) {
    return "Хранилище фотографий временно недоступно";
  }
  if (apiError.status === 0) {
    return "Не удалось подключиться к серверу";
  }
  return "Не удалось выполнить запрос";
}
