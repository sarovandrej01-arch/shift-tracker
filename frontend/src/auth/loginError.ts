import { ApiError } from "../types/api.ts";
import { normalizeApiError } from "../api/errors.ts";

export function getLoginErrorMessage(error: unknown): string {
  const apiError = error instanceof ApiError ? error : normalizeApiError(error);

  if (apiError.status === 401) {
    return "Неверный email или пароль";
  }
  if (apiError.status === 403) {
    return "Пользователь отключён";
  }
  if (apiError.status === 0) {
    return "Не удалось подключиться к серверу";
  }
  return "Не удалось войти";
}
