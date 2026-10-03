export type DashboardPeriod = {
  date_from: string | null;
  date_to: string | null;
};

export type DashboardMessageCounts = {
  total: number;
  new: number;
  processing: number;
  accepted: number;
  review: number;
  rejected: number;
  duplicate: number;
  error: number;
};

export type DashboardShiftCounts = {
  total: number;
  automatic: number;
  manual: number;
};

export type DashboardObjectSummary = {
  object_id: number;
  object_name: string;
  messages_total: number;
  accepted: number;
  review: number;
  rejected: number;
  shifts_total: number;
};

export type DashboardSummary = {
  period: DashboardPeriod;
  messages: DashboardMessageCounts;
  shifts: DashboardShiftCounts;
  by_object: DashboardObjectSummary[];
};

export type DashboardFilters = {
  dateFrom: string;
  dateTo: string;
  objectId: string;
};
