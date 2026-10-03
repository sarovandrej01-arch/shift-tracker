import { apiClient } from "./client.ts";

type HealthResponse = {
  status: string;
};

export async function fetchApiHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>("/api/test/health");
  return response.data;
}
