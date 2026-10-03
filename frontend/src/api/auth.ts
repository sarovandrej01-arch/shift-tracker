import { apiClient } from "./client.ts";
import { getAccessToken } from "../auth/tokenStorage.ts";
import type { LoginRequest, LoginResponse } from "../types/auth.ts";
import type { User } from "../types/user.ts";

let currentUserRequest: { token: string; promise: Promise<User> } | null = null;

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>("/api/v1/auth/login", {
    email: credentials.email,
    password: credentials.password,
  });
  return response.data;
}

export function getCurrentUser(): Promise<User> {
  const token = getAccessToken() ?? "";
  if (currentUserRequest?.token === token) {
    return currentUserRequest.promise;
  }

  const promise = apiClient
    .get<User>("/api/v1/auth/me")
    .then((response) => response.data)
    .finally(() => {
      if (currentUserRequest?.promise === promise) {
        currentUserRequest = null;
      }
    });

  currentUserRequest = { token, promise };
  return promise;
}
