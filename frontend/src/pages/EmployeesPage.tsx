import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { activateEmployee, createEmployee, deactivateEmployee, updateEmployee } from "../api/employees.ts";
import { canAccessAdmin } from "../auth/roles.ts";
import { ActiveBadge } from "../components/ActiveBadge.tsx";
import { EmployeeForm } from "../components/EmployeeForm.tsx";
import { EmptyState } from "../components/EmptyState.tsx";
import { ErrorState } from "../components/ErrorState.tsx";
import { Field, SelectInput, TextInput } from "../components/Field.tsx";
import { FilterBar } from "../components/FilterBar.tsx";
import { LoadingState } from "../components/LoadingState.tsx";
import { Modal } from "../components/Modal.tsx";
import { PageHeader } from "../components/PageHeader.tsx";
import { PaginationControls } from "../components/PaginationControls.tsx";
import { useAuth } from "../hooks/useAuth.ts";
import { useEmployeeList } from "../hooks/useDirectoryLists.ts";
import { getApiErrorMessage } from "../lib/apiErrorMessage.ts";
import { formatDateTime } from "../lib/format.ts";
import { queryClient } from "../lib/queryClient.ts";
import { buttonClass } from "../lib/ui.ts";
import type { Employee, EmployeeFilters, EmployeeWrite } from "../types/directory.ts";
import { PAGE_SIZE } from "../types/message.ts";

const EMPTY_FILTERS: EmployeeFilters = { isActive: "", search: "", offset: 0 };

export function EmployeesPage() {
  const { user } = useAuth();
  const isAdmin = canAccessAdmin(user);
  const [filters, setFilters] = useState<EmployeeFilters>(EMPTY_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [editing, setEditing] = useState<Employee | null | "create">(null);
  const [deactivateTarget, setDeactivateTarget] = useState<Employee | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const employees = useEmployeeList(filters);

  function updateFilters(patch: Partial<EmployeeFilters>) {
    setFilters((current) => ({ ...current, ...patch, offset: patch.offset ?? 0 }));
  }

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["employees"] });
  }

  const saveMutation = useMutation({
    mutationFn: (data: EmployeeWrite) =>
      editing && editing !== "create" ? updateEmployee(editing.id, data) : createEmployee(data),
    onSuccess: async () => {
      setEditing(null);
      setFormError(null);
      setNotice(editing === "create" ? "Сотрудник добавлен" : "Сотрудник обновлён");
      await refresh();
    },
    onError: (error) => setFormError(getApiErrorMessage(error)),
  });

  const activationMutation = useMutation({
    mutationFn: (employee: Employee) =>
      employee.is_active ? deactivateEmployee(employee.id) : activateEmployee(employee.id),
    onSuccess: async (_result, employee) => {
      setDeactivateTarget(null);
      setNotice(employee.is_active ? "Сотрудник деактивирован" : "Сотрудник активирован");
      await refresh();
    },
    onError: (error) => setNotice(getApiErrorMessage(error)),
  });

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <PageHeader title="Employees" description="Сотрудники, которых можно указать в смене" />
        {isAdmin ? (
          <button type="button" className={`${buttonClass.primary} w-full shrink-0 sm:w-auto`} onClick={() => { setFormError(null); setEditing("create"); }}>
            Добавить сотрудника
          </button>
        ) : null}
      </div>
      <button type="button" className={`${buttonClass.secondary} mb-3 md:hidden`} onClick={() => setFiltersOpen((open) => !open)}>
        {filtersOpen ? "Скрыть фильтры" : "Фильтры"}
      </button>
      <div className={filtersOpen ? "mb-4 block" : "mb-4 hidden md:block"}>
        <FilterBar>
          <Field label="Поиск" htmlFor="employee-search">
            <TextInput
              id="employee-search"
              value={filters.search}
              placeholder="ФИО, табельный, позывной, Telegram"
              onChange={(event) => updateFilters({ search: event.target.value })}
            />
          </Field>
          <Field label="Статус" htmlFor="employee-active">
            <SelectInput
              id="employee-active"
              value={filters.isActive}
              onChange={(event) => updateFilters({ isActive: event.target.value as EmployeeFilters["isActive"] })}
            >
              <option value="">Все</option>
              <option value="true">Активные</option>
              <option value="false">Неактивные</option>
            </SelectInput>
          </Field>
          <div className="flex items-end">
            <button type="button" className={`${buttonClass.secondary} w-full`} onClick={() => updateFilters(EMPTY_FILTERS)}>
              Сбросить фильтры
            </button>
          </div>
        </FilterBar>
      </div>
      {notice ? <p className="mb-4 rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-800" role="status">{notice}</p> : null}
      {employees.isLoading ? <LoadingState variant="table" /> : null}
      {employees.isError ? <ErrorState error={employees.error} onRetry={() => void employees.refetch()} /> : null}
      {employees.data && employees.data.length === 0 ? <EmptyState title="Сотрудники не найдены" /> : null}
      {employees.data && employees.data.length > 0 ? (
        <>
          <div className="space-y-3 md:hidden">
            {employees.data.map((employee) => (
              <article key={employee.id} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-sm font-medium">{employee.full_name}</h2>
                    <p className="text-xs text-slate-500">{employee.personnel_number}</p>
                  </div>
                  <ActiveBadge active={employee.is_active} />
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  {employee.callsign ?? "Без позывного"} · {employee.telegram_username ?? "без Telegram"} ·{" "}
                  {employee.telegram_user_id ?? "—"}
                </p>
                <p className="mt-1 text-xs text-slate-500">{formatDateTime(employee.created_at)}</p>
                {isAdmin ? <EmployeeActions employee={employee} pending={activationMutation.isPending} onEdit={() => { setFormError(null); setEditing(employee); }} onToggle={() => employee.is_active ? setDeactivateTarget(employee) : activationMutation.mutate(employee)} /> : null}
              </article>
            ))}
          </div>
          <div className="hidden overflow-x-auto md:block">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-2 py-2 font-medium">ФИО</th>
                  <th className="px-2 py-2 font-medium">Табельный</th>
                  <th className="px-2 py-2 font-medium">Позывной</th>
                  <th className="px-2 py-2 font-medium">Telegram</th>
                  <th className="px-2 py-2 font-medium">Telegram ID</th>
                  <th className="px-2 py-2 font-medium">Статус</th>
                  <th className="px-2 py-2 font-medium">Создан</th>
                  {isAdmin ? <th className="px-2 py-2 font-medium">Действия</th> : null}
                </tr>
              </thead>
              <tbody>
                {employees.data.map((employee) => (
                  <tr key={employee.id} className="border-b border-slate-100">
                    <td className="px-2 py-2">{employee.full_name}</td>
                    <td className="px-2 py-2">{employee.personnel_number}</td>
                    <td className="px-2 py-2">{employee.callsign ?? "—"}</td>
                    <td className="px-2 py-2">{employee.telegram_username ?? "—"}</td>
                    <td className="px-2 py-2">{employee.telegram_user_id ?? "—"}</td>
                    <td className="px-2 py-2"><ActiveBadge active={employee.is_active} /></td>
                    <td className="px-2 py-2">{formatDateTime(employee.created_at)}</td>
                    {isAdmin ? (
                      <td className="px-2 py-2">
                        <EmployeeActions employee={employee} pending={activationMutation.isPending} onEdit={() => { setFormError(null); setEditing(employee); }} onToggle={() => employee.is_active ? setDeactivateTarget(employee) : activationMutation.mutate(employee)} />
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <PaginationControls offset={filters.offset} limit={PAGE_SIZE} count={employees.data.length} onOffsetChange={(offset) => updateFilters({ offset })} />
        </>
      ) : null}
      <Modal title={editing === "create" ? "Новый сотрудник" : "Редактирование сотрудника"} open={editing !== null} onClose={() => setEditing(null)}>
        {editing !== null ? (
          <EmployeeForm
            key={editing === "create" ? "create" : editing.id}
            employee={editing === "create" ? null : editing}
            pending={saveMutation.isPending}
            error={formError}
            onCancel={() => setEditing(null)}
            onSubmit={(data) => saveMutation.mutate(data)}
          />
        ) : null}
      </Modal>
      <Modal title="Деактивировать сотрудника?" open={deactivateTarget !== null} onClose={() => setDeactivateTarget(null)}>
        <p className="text-sm text-slate-600">{deactivateTarget?.full_name} больше не будет доступен для новых смен.</p>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <button type="button" className={`${buttonClass.danger} w-full sm:w-auto`} disabled={activationMutation.isPending} onClick={() => deactivateTarget && activationMutation.mutate(deactivateTarget)}>
            Деактивировать
          </button>
          <button type="button" className={`${buttonClass.secondary} w-full sm:w-auto`} onClick={() => setDeactivateTarget(null)}>
            Отмена
          </button>
        </div>
      </Modal>
    </div>
  );
}

function EmployeeActions({
  employee,
  pending,
  onEdit,
  onToggle,
}: {
  employee: Employee;
  pending: boolean;
  onEdit: () => void;
  onToggle: () => void;
}) {
  return (
    <div className="mt-3 flex flex-col gap-2 sm:mt-0 sm:flex-row">
      <button type="button" className={buttonClass.secondary} onClick={onEdit}>
        Изменить
      </button>
      <button type="button" className={employee.is_active ? buttonClass.danger : buttonClass.primary} disabled={pending} onClick={onToggle}>
        {employee.is_active ? "Деактивировать" : "Активировать"}
      </button>
    </div>
  );
}
