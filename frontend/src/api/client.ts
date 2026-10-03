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

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    const apiError = normalizeApiError(error);
    if (apiError.status === 401) {
      clearAccessToken();
      notifyUnauthorized();
    }
    return Promise.reject(apiError);
  },
);
