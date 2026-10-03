import type {
  ReviewConfirmRequest,
  ReviewConfirmResponse,
  ReviewFilters,
  ReviewMessage,
  ReviewRejectRequest,
  ReviewRejectResponse,
} from "../types/message.ts";
import { PAGE_SIZE } from "../types/message.ts";
import { apiClient } from "./client.ts";
import { definedParams } from "./params.ts";

export async function listReviews(filters: ReviewFilters): Promise<ReviewMessage[]> {
  const response = await apiClient.get<ReviewMessage[]>("/api/v1/reviews", {
    params: definedParams({
      offset: filters.offset,
      limit: PAGE_SIZE,
      reason: filters.reason,
      employee_id: filters.employeeId ? Number(filters.employeeId) : undefined,
      object_id: filters.objectId ? Number(filters.objectId) : undefined,
      date_from: filters.dateFrom,
      date_to: filters.dateTo,
    }),
  });
  return response.data;
}

export async function confirmReview(
  messageId: number,
  body: ReviewConfirmRequest,
): Promise<ReviewConfirmResponse> {
  const response = await apiClient.post<ReviewConfirmResponse>(
    `/api/v1/reviews/${messageId}/confirm`,
    body,
  );
  return response.data;
}

export async function rejectReview(
  messageId: number,
  body: ReviewRejectRequest,
): Promise<ReviewRejectResponse> {
  const response = await apiClient.post<ReviewRejectResponse>(
    `/api/v1/reviews/${messageId}/reject`,
    body,
  );
  return response.data;
}
