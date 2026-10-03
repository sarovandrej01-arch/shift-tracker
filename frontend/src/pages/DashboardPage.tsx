import { useState } from "react";

import { EmptyState } from "../components/EmptyState.tsx";
import { ErrorState } from "../components/ErrorState.tsx";
import { Field, SelectInput, TextInput } from "../components/Field.tsx";
import { FilterBar } from "../components/FilterBar.tsx";
import { LoadingState } from "../components/LoadingState.tsx";
import { PageHeader } from "../components/PageHeader.tsx";
import { useDashboardSummary } from "../hooks/useDashboardSummary.ts";
import { useWorkObjects } from "../hooks/useDirectories.ts";
import { formatPeriod } from "../lib/format.ts";
import { buttonClass } from "../lib/ui.ts";
import type { DashboardFilters, DashboardMessageCounts, DashboardObjectSummary } from "../types/dashboard.ts";

const EMPTY_FILTERS: DashboardFilters = { dateFrom: "", dateTo: "", objectId: "" };

const MESSAGE_CARDS: { key: keyof DashboardMessageCounts; label: string }[] = [
  { key: "total", label: "Всего" },
  { key: "new", label: "Новые" },
  { key: "processing", label: "В обработке" },
  { key: "accepted", label: "Принятые" },
  { key: "review", label: "На проверке" },
  { key: "rejected", label: "Отклонённые" },
  { key: "duplicate", label: "Дубликаты" },
  { key: "error", label: "Ошибки" },
];

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm text-slate-600">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function ObjectCards({ rows }: { rows: DashboardObjectSummary[] }) {
  return (
    <div className="space-y-3 md:hidden">
      {rows.map((row) => (
        <article key={row.object_id} className="rounded-lg border border-slate-200 p-3">
          <h3 className="font-medium">{row.object_name}</h3>
          <dl className="mt-2 grid grid-cols-2 gap-2 text-sm">
            <div>
              <dt className="text-slate-500">Сообщения</dt>
              <dd>{row.messages_total}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Принято</dt>
              <dd>{row.accepted}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Проверка</dt>
              <dd>{row.review}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Отклонено</dt>
              <dd>{row.rejected}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Смены</dt>
              <dd>{row.shifts_total}</dd>
            </div>
          </dl>
        </article>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const [filters, setFilters] = useState<DashboardFilters>(EMPTY_FILTERS);
  const summary = useDashboardSummary(filters);
  const workObjects = useWorkObjects();

  return (
    <div>
      <PageHeader title="Dashboard" description="Сводка сообщений и смен за период" />
      <FilterBar>
        <Field label="Дата с" htmlFor="dashboard-date-from">
          <TextInput
            id="dashboard-date-from"
            type="date"
            value={filters.dateFrom}
            onChange={(event) => setFilters((current) => ({ ...current, dateFrom: event.target.value }))}
          />
        </Field>
        <Field label="Дата по" htmlFor="dashboard-date-to">
          <TextInput
            id="dashboard-date-to"
            type="date"
            value={filters.dateTo}
            onChange={(event) => setFilters((current) => ({ ...current, dateTo: event.target.value }))}
          />
        </Field>
        <Field label="Объект" htmlFor="dashboard-object">
          <SelectInput
            id="dashboard-object"
            value={filters.objectId}
            onChange={(event) => setFilters((current) => ({ ...current, objectId: event.target.value }))}
          >
            <option value="">Все объекты</option>
            {(workObjects.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </SelectInput>
        </Field>
        <div className="flex items-end">
          <button type="button" className={`${buttonClass.secondary} w-full`} onClick={() => setFilters(EMPTY_FILTERS)}>
            Сбросить фильтры
          </button>
        </div>
      </FilterBar>

      <div className="mt-6">
        {summary.isLoading ? <LoadingState variant="cards" /> : null}
        {summary.isError ? <ErrorState error={summary.error} onRetry={() => void summary.refetch()} /> : null}
        {summary.data ? (
          <div className="space-y-6">
            <p className="text-sm text-slate-600">
              Период: {formatPeriod(summary.data.period.date_from, summary.data.period.date_to)}
            </p>
            <section>
              <h2 className="mb-3 text-sm font-semibold text-slate-700">Сообщения</h2>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
                {MESSAGE_CARDS.map((card) => (
                  <StatCard key={card.key} label={card.label} value={summary.data.messages[card.key]} />
                ))}
              </div>
            </section>
            <section>
              <h2 className="mb-3 text-sm font-semibold text-slate-700">Смены</h2>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <StatCard label="Всего" value={summary.data.shifts.total} />
                <StatCard label="Автоматические" value={summary.data.shifts.automatic} />
                <StatCard label="Ручные" value={summary.data.shifts.manual} />
              </div>
            </section>
            <section>
              <h2 className="mb-3 text-sm font-semibold text-slate-700">По объектам</h2>
              {summary.data.by_object.length === 0 ? (
                <EmptyState title="Нет данных по объектам" />
              ) : (
                <>
                  <ObjectCards rows={summary.data.by_object} />
                  <div className="hidden overflow-x-auto md:block">
                    <table className="min-w-full text-left text-sm">
                      <thead className="border-b border-slate-200 text-slate-500">
                        <tr>
                          <th className="px-2 py-2 font-medium">Объект</th>
                          <th className="px-2 py-2 font-medium">Сообщения</th>
                          <th className="px-2 py-2 font-medium">Принято</th>
                          <th className="px-2 py-2 font-medium">Проверка</th>
                          <th className="px-2 py-2 font-medium">Отклонено</th>
                          <th className="px-2 py-2 font-medium">Смены</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.data.by_object.map((row) => (
                          <tr key={row.object_id} className="border-b border-slate-100">
                            <td className="px-2 py-2">{row.object_name}</td>
                            <td className="px-2 py-2">{row.messages_total}</td>
                            <td className="px-2 py-2">{row.accepted}</td>
                            <td className="px-2 py-2">{row.review}</td>
                            <td className="px-2 py-2">{row.rejected}</td>
                            <td className="px-2 py-2">{row.shifts_total}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </section>
          </div>
        ) : null}
      </div>
    </div>
  );
}
