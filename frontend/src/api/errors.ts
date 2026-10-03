import axios from "axios";

import { ApiError } from "../types/api.ts";

function readDetail(data: unknown): string | null {
  if (typeof data !== "object" || data === null || !("detail" in data)) {
    return null;
  }

  const { detail } = data;
  if (typeof detail === "string") {
    return detail;
  }

  if (!Array.isArray(detail)) {
    return null;
  }

  const messages = detail.flatMap((item: unknown) => {
    if (typeof item === "string") {
      return [item];
    }
    if (
      typeof item === "object" &&
      item !== null &&
      "msg" in item &&
      typeof item.msg === "string"
    ) {
      return [item.msg];
    }
    return [];
  });

  return messages.length > 0 ? messages.join("; ") : null;
}

export function normalizeApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? 0;
    const detail = readDetail(error.response?.data);
    const message = status === 403 ? "Недостаточно прав" : (detail ?? error.message);
    return new ApiError(status, message, detail);
  }

  if (error instanceof Error) {
    return new ApiError(0, error.message, null);
  }

  return new ApiError(0, "Не удалось выполнить запрос", null);
}
