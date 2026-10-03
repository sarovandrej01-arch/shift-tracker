import { useQuery } from "@tanstack/react-query";

import { listReviews } from "../api/reviews.ts";
import { queryKeys } from "../lib/queryKeys.ts";
import type { ReviewFilters } from "../types/message.ts";

export function useReviews(filters: ReviewFilters) {
  return useQuery({
    queryKey: queryKeys.reviews(filters),
    queryFn: () => listReviews(filters),
  });
}
