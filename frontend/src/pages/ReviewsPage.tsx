import { useState } from "react";

import { EmptyState } from "../components/EmptyState.tsx";
import { ErrorState } from "../components/ErrorState.tsx";
import { Field, SelectInput, TextInput } from "../components/Field.tsx";
import { FilterBar } from "../components/FilterBar.tsx";
import { LoadingState } from "../components/LoadingState.tsx";
import { PageHeader } from "../components/PageHeader.tsx";
import { PaginationControls } from "../components/PaginationControls.tsx";
import { ReviewDetail } from "../components/ReviewDetail.tsx";
import { StatusBadge } from "../components/StatusBadge.tsx";
import { useEmployees, useWorkObjects } from "../hooks/useDirectories.ts";
import { useReviews } from "../hooks/useReviews.ts";
import { formatDateTime, formatMessageReason, formatTelegramUser, messagePreview } from "../lib/format.ts";
import { buttonClass } from "../lib/ui.ts";
import type { MessageReason, ReviewFilters } from "../types/message.ts";
import { PAGE_SIZE } from "../types/message.ts";

const REASONS: MessageReason[] = [
  "no_photo",
  "employee_not_found",
  "employee_ambiguous",
  "group_not_configured",
  "outside_shift_window",
  "shift_already_exists",
  "message_already_processed",
  "internal_error",
];

const EMPTY_FILTERS: ReviewFilters = {
  reason: "",
  employeeId: "",
  objectId: "",
  dateFrom: "",
  dateTo: "",
  offset: 0,
};

export function ReviewsPage() {
  const [filters, setFilters] = useState<ReviewFilters>(EMPTY_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const reviews = useReviews(filters);
  const employees = useEmployees();
  const workObjects = useWorkObjects();
  const selected = reviews.data?.find((item) => item.id === selectedId) ?? null;
  const employeeNames = new Map((employees.data ?? []).map((item) => [item.id, item.full_name]));
  const objectNames = new Map((workObjects.data ?? []).map((item) => [item.id, item.name]));

  function updateFilters(patch: Partial<ReviewFilters>) {
    setFilters((current) => ({ ...current, ...patch, offset: patch.offset ?? 0 }));
    setSelectedId(null);
  }

  return (
    <div>
      <PageHeader title="Reviews" description="Сообщения, которые ждут решения модератора" />
      <button
        type="button"
        className={`${buttonClass.secondary} mb-3 md:hidden`}
        onClick={() => setFiltersOpen((open) => !open)}
      >
        {filtersOpen ? "Скрыть фильтры" : "Фильтры"}
      </button>
      <div className={filtersOpen ? "mb-4 block" : "mb-4 hidden md:block"}>
        <FilterBar>
          <Field label="Причина" htmlFor="review-reason">
            <SelectInput
              id="review-reason"
              value={filters.reason}
              onChange={(event) => updateFilters({ reason: event.target.value })}
            >
              <option value="">Все</option>
              {REASONS.map((reason) => (
                <option key={reason} value={reason}>
                  {formatMessageReason(reason)}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Сотрудник" htmlFor="review-employee-filter">
            <SelectInput
              id="review-employee-filter"
              value={filters.employeeId}
              onChange={(event) => updateFilters({ employeeId: event.target.value })}
            >
              <option value="">Все</option>
              {(employees.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.full_name}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Объект" htmlFor="review-object-filter">
            <SelectInput
              id="review-object-filter"
              value={filters.objectId}
              onChange={(event) => updateFilters({ objectId: event.target.value })}
            >
              <option value="">Все</option>
              {(workObjects.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Дата с" htmlFor="review-date-from">
            <TextInput
              id="review-date-from"
              type="date"
              value={filters.dateFrom}
              onChange={(event) => updateFilters({ dateFrom: event.target.value })}
            />
          </Field>
          <Field label="Дата по" htmlFor="review-date-to">
            <TextInput
              id="review-date-to"
              type="date"
              value={filters.dateTo}
              onChange={(event) => updateFilters({ dateTo: event.target.value })}
            />
          </Field>
          <div className="flex items-end">
            <button type="button" className={`${buttonClass.secondary} w-full`} onClick={() => updateFilters(EMPTY_FILTERS)}>
              Сбросить фильтры
            </button>
          </div>
        </FilterBar>
      </div>
      {notice ? (
        <p className="mb-4 rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-800" role="status">
          {notice}
        </p>
      ) : null}
      {reviews.isLoading ? <LoadingState /> : null}
      {reviews.isError ? <ErrorState error={reviews.error} onRetry={() => void reviews.refetch()} /> : null}
      {reviews.data ? (
        reviews.data.length === 0 ? (
          <EmptyState title="Нет сообщений на проверке" />
        ) : (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className={selected ? "hidden space-y-3 lg:block" : "space-y-3"}>
              {reviews.data.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`w-full rounded-lg border p-3 text-left ${
                    item.id === selected?.id ? "border-slate-900" : "border-slate-200"
                  }`}
                  onClick={() => {
                    setSelectedId(item.id);
                    setNotice(null);
                  }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium">#{item.id}</span>
                    <StatusBadge status={item.status} />
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm">{messagePreview(item.text, item.caption)}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    {formatTelegramUser(item.telegram_username, item.telegram_user_id)}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">{formatMessageReason(item.reason)}</p>
                  <p className="mt-1 text-xs text-slate-500">{formatDateTime(item.created_at)}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {item.employee_id ? (employeeNames.get(item.employee_id) ?? `Сотрудник #${item.employee_id}`) : "Сотрудник не указан"}
                    {" · "}
                    {item.object_id ? (objectNames.get(item.object_id) ?? `Объект #${item.object_id}`) : "Объект не указан"}
                  </p>
                </button>
              ))}
              <PaginationControls
                offset={filters.offset}
                limit={PAGE_SIZE}
                count={reviews.data.length}
                onOffsetChange={(offset) => updateFilters({ offset })}
              />
            </div>
            <div className={selected ? "block" : "hidden lg:block"}>
              {selected ? (
                <ReviewDetail
                  key={selected.id}
                  message={selected}
                  onBack={() => setSelectedId(null)}
                  onDone={(message) => {
                    setNotice(message);
                    setSelectedId(null);
                  }}
                />
              ) : (
                <EmptyState title="Выберите сообщение" />
              )}
            </div>
          </div>
        )
      ) : null}
    </div>
  );
}
