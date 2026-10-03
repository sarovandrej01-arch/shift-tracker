import { useState } from "react";

import { ConfirmationBadge } from "../components/ActiveBadge.tsx";
import { EmptyState } from "../components/EmptyState.tsx";
import { ErrorState } from "../components/ErrorState.tsx";
import { Field, SelectInput, TextInput } from "../components/Field.tsx";
import { FilterBar } from "../components/FilterBar.tsx";
import { LoadingState } from "../components/LoadingState.tsx";
import { Modal } from "../components/Modal.tsx";
import { PageHeader } from "../components/PageHeader.tsx";
import { PaginationControls } from "../components/PaginationControls.tsx";
import { ShiftDetailView } from "../components/ShiftDetailView.tsx";
import { useEmployees, useWorkObjects } from "../hooks/useDirectories.ts";
import { useShifts } from "../hooks/useShifts.ts";
import { formatDate, formatDateTime } from "../lib/format.ts";
import { buttonClass } from "../lib/ui.ts";
import { PAGE_SIZE } from "../types/message.ts";
import type { Shift } from "../types/message.ts";
import type { ShiftFilters } from "../types/shift.ts";

const EMPTY_FILTERS: ShiftFilters = {
  employeeId: "",
  objectId: "",
  dateFrom: "",
  dateTo: "",
  confirmedManually: "",
  offset: 0,
};

export function ShiftsPage() {
  const [filters, setFilters] = useState<ShiftFilters>(EMPTY_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const shifts = useShifts(filters);
  const employees = useEmployees();
  const workObjects = useWorkObjects();
  const employeeNames = new Map((employees.data ?? []).map((item) => [item.id, item.full_name]));
  const objectNames = new Map((workObjects.data ?? []).map((item) => [item.id, item.name]));

  function updateFilters(patch: Partial<ShiftFilters>) {
    setFilters((current) => ({ ...current, ...patch, offset: patch.offset ?? 0 }));
  }

  function employeeLabel(shift: Shift): string {
    return employeeNames.get(shift.employee_id) ?? `#${shift.employee_id}`;
  }

  function objectLabel(shift: Shift): string {
    return objectNames.get(shift.object_id) ?? `#${shift.object_id}`;
  }

  return (
    <div>
      <PageHeader title="Shifts" description="Подтверждённые смены" />
      <button type="button" className={`${buttonClass.secondary} mb-3 md:hidden`} onClick={() => setFiltersOpen((open) => !open)}>
        {filtersOpen ? "Скрыть фильтры" : "Фильтры"}
      </button>
      <div className={filtersOpen ? "mb-4 block" : "mb-4 hidden md:block"}>
        <FilterBar>
          <Field label="Сотрудник" htmlFor="shift-employee">
            <SelectInput id="shift-employee" value={filters.employeeId} onChange={(event) => updateFilters({ employeeId: event.target.value })}>
              <option value="">Все</option>
              {(employees.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.full_name}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Объект" htmlFor="shift-object">
            <SelectInput id="shift-object" value={filters.objectId} onChange={(event) => updateFilters({ objectId: event.target.value })}>
              <option value="">Все</option>
              {(workObjects.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Дата с" htmlFor="shift-date-from">
            <TextInput id="shift-date-from" type="date" value={filters.dateFrom} onChange={(event) => updateFilters({ dateFrom: event.target.value })} />
          </Field>
          <Field label="Дата по" htmlFor="shift-date-to">
            <TextInput id="shift-date-to" type="date" value={filters.dateTo} onChange={(event) => updateFilters({ dateTo: event.target.value })} />
          </Field>
          <Field label="Подтверждение" htmlFor="shift-manual">
            <SelectInput
              id="shift-manual"
              value={filters.confirmedManually}
              onChange={(event) => updateFilters({ confirmedManually: event.target.value as ShiftFilters["confirmedManually"] })}
            >
              <option value="">Все</option>
              <option value="false">Автоматические</option>
              <option value="true">Ручные</option>
            </SelectInput>
          </Field>
          <div className="flex items-end">
            <button type="button" className={`${buttonClass.secondary} w-full`} onClick={() => updateFilters(EMPTY_FILTERS)}>
              Сбросить фильтры
            </button>
          </div>
        </FilterBar>
      </div>
      {shifts.isLoading ? <LoadingState variant="table" /> : null}
      {shifts.isError ? <ErrorState error={shifts.error} onRetry={() => void shifts.refetch()} /> : null}
      {shifts.data && shifts.data.length === 0 ? <EmptyState title="Смены не найдены" /> : null}
      {shifts.data && shifts.data.length > 0 ? (
        <>
          <div className="space-y-3 md:hidden">
            {shifts.data.map((shift) => (
              <button
                key={shift.id}
                type="button"
                className="w-full rounded-lg border border-slate-200 p-3 text-left"
                onClick={() => setSelectedId(shift.id)}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">#{shift.id}</span>
                  <ConfirmationBadge manual={shift.confirmed_manually} />
                </div>
                <p className="mt-2 text-sm">{employeeLabel(shift)}</p>
                <p className="mt-1 text-xs text-slate-500">{objectLabel(shift)}</p>
                <p className="mt-1 text-xs text-slate-500">{formatDate(shift.shift_date)}</p>
              </button>
            ))}
          </div>
          <div className="hidden overflow-x-auto md:block">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-2 py-2 font-medium">ID</th>
                  <th className="px-2 py-2 font-medium">Сотрудник</th>
                  <th className="px-2 py-2 font-medium">Объект</th>
                  <th className="px-2 py-2 font-medium">Дата</th>
                  <th className="px-2 py-2 font-medium">Подтверждение</th>
                  <th className="px-2 py-2 font-medium">Кем</th>
                  <th className="px-2 py-2 font-medium">Сообщение</th>
                  <th className="px-2 py-2 font-medium">Создано</th>
                </tr>
              </thead>
              <tbody>
                {shifts.data.map((shift) => (
                  <tr
                    key={shift.id}
                    tabIndex={0}
                    className="cursor-pointer border-b border-slate-100 hover:bg-slate-50"
                    onClick={() => setSelectedId(shift.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setSelectedId(shift.id);
                      }
                    }}
                  >
                    <td className="px-2 py-2">{shift.id}</td>
                    <td className="px-2 py-2">{employeeLabel(shift)}</td>
                    <td className="px-2 py-2">{objectLabel(shift)}</td>
                    <td className="px-2 py-2">{formatDate(shift.shift_date)}</td>
                    <td className="px-2 py-2">
                      <ConfirmationBadge manual={shift.confirmed_manually} />
                    </td>
                    <td className="px-2 py-2">{shift.confirmed_by_user_id === null ? "—" : `#${shift.confirmed_by_user_id}`}</td>
                    <td className="px-2 py-2">{shift.source_message_id === null ? "—" : `#${shift.source_message_id}`}</td>
                    <td className="px-2 py-2">{formatDateTime(shift.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <PaginationControls
            offset={filters.offset}
            limit={PAGE_SIZE}
            count={shifts.data.length}
            onOffsetChange={(offset) => updateFilters({ offset })}
          />
        </>
      ) : null}
      <Modal title={selectedId === null ? "Смена" : `Смена ${selectedId}`} open={selectedId !== null} onClose={() => setSelectedId(null)}>
        {selectedId !== null ? <ShiftDetailView shiftId={selectedId} /> : null}
      </Modal>
    </div>
  );
}
