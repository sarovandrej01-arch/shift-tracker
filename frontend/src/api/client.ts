import axios from "axios";

import { notifyUnauthorized } from "../auth/session.ts";
import { clearAccessToken, getAccessToken } from "../auth/tokenStorage.ts";
import { API_BASE_URL } from "../lib/config.ts";
import { normalizeApiError } from "./errors.ts";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function readBearerToken(error: unknown): string | null {
  if (!axios.isAxiosError(error)) {
    return null;
  }

  const headers = error.config?.headers;
  if (!headers) {
    return null;
  }

  const value =
    typeof headers.get === "function"
      ? headers.get("Authorization")
      : headers.Authorization;
  if (typeof value !== "string") {
    return null;
  }

  const prefix = "Bearer ";
  return value.startsWith(prefix) ? value.slice(prefix.length) : null;
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    const apiError = normalizeApiError(error);
    if (apiError.status === 401) {
      const requestToken = readBearerToken(error);
      const storedToken = getAccessToken();
      const tokenStillCurrent = requestToken === null || requestToken === storedToken;
      if (tokenStillCurrent) {
        clearAccessToken();
        notifyUnauthorized();
      }
    }
    return Promise.reject(apiError);
  },
);
