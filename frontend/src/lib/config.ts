const DEV_API_BASE_URL = "http://127.0.0.1:8000";

function readApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (typeof configured === "string") {
    return configured.trim().replace(/\/$/, "");
  }
  return DEV_API_BASE_URL;
}

export const API_BASE_URL = readApiBaseUrl();
