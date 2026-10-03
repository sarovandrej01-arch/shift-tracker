import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { activateWorkObject, createWorkObject, deactivateWorkObject, updateWorkObject } from "../api/workObjects.ts";
import { canAccessAdmin } from "../auth/roles.ts";
import { ActiveBadge } from "../components/ActiveBadge.tsx";
import { EmptyState } from "../components/EmptyState.tsx";
import { ErrorState } from "../components/ErrorState.tsx";
import { Field, SelectInput, TextInput } from "../components/Field.tsx";
import { FilterBar } from "../components/FilterBar.tsx";
import { LoadingState } from "../components/LoadingState.tsx";
import { Modal } from "../components/Modal.tsx";
import { PageHeader } from "../components/PageHeader.tsx";
import { PaginationControls } from "../components/PaginationControls.tsx";
import { WorkObjectForm } from "../components/WorkObjectForm.tsx";
import { useAuth } from "../hooks/useAuth.ts";
import { useWorkObjectList } from "../hooks/useDirectoryLists.ts";
import { getApiErrorMessage } from "../lib/apiErrorMessage.ts";
import { formatTime } from "../lib/format.ts";
import { queryClient } from "../lib/queryClient.ts";
import { buttonClass } from "../lib/ui.ts";
import type { WorkObject, WorkObjectFilters, WorkObjectWrite } from "../types/directory.ts";
import { PAGE_SIZE } from "../types/message.ts";

const EMPTY_FILTERS: WorkObjectFilters = { isActive: "", search: "", offset: 0 };

export function WorkObjectsPage() {
  const { user } = useAuth();
  const isAdmin = canAccessAdmin(user);
  const [filters, setFilters] = useState<WorkObjectFilters>(EMPTY_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [editing, setEditing] = useState<WorkObject | null | "create">(null);
  const [deactivateTarget, setDeactivateTarget] = useState<WorkObject | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const objects = useWorkObjectList(filters);

  function updateFilters(patch: Partial<WorkObjectFilters>) {
    setFilters((current) => ({ ...current, ...patch, offset: patch.offset ?? 0 }));
  }

  async function refresh() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["work-objects"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      queryClient.invalidateQueries({ queryKey: ["reviews"] }),
      queryClient.invalidateQueries({ queryKey: ["messages"] }),
    ]);
  }

  const saveMutation = useMutation({
    mutationFn: (data: WorkObjectWrite) =>
      editing && editing !== "create" ? updateWorkObject(editing.id, data) : createWorkObject(data),
    onSuccess: async () => {
      setEditing(null);
      setFormError(null);
      setNotice(editing === "create" ? "Объект добавлен" : "Объект обновлён");
      await refresh();
    },
    onError: (error) => setFormError(getApiErrorMessage(error)),
  });

  const activationMutation = useMutation({
    mutationFn: (workObject: WorkObject) =>
      workObject.is_active ? deactivateWorkObject(workObject.id) : activateWorkObject(workObject.id),
    onSuccess: async (_result, workObject) => {
      setDeactivateTarget(null);
      setNotice(workObject.is_active ? "Объект деактивирован" : "Объект активирован");
      await refresh();
    },
    onError: (error) => setNotice(getApiErrorMessage(error)),
  });

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <PageHeader title="Work Objects" description="Объекты и окно отметки смены" />
        {isAdmin ? (
          <button type="button" className={`${buttonClass.primary} w-full shrink-0 sm:w-auto`} onClick={() => { setFormError(null); setEditing("create"); }}>
            Добавить объект
          </button>
        ) : null}
      </div>
      <button type="button" className={`${buttonClass.secondary} mb-3 md:hidden`} onClick={() => setFiltersOpen((open) => !open)}>
        {filtersOpen ? "Скрыть фильтры" : "Фильтры"}
      </button>
      <div className={filtersOpen ? "mb-4 block" : "mb-4 hidden md:block"}>
        <FilterBar>
          <Field label="Поиск" htmlFor="object-search">
            <TextInput
              id="object-search"
              value={filters.search}
              placeholder="Название или часовой пояс"
              onChange={(event) => updateFilters({ search: event.target.value })}
            />
          </Field>
          <Field label="Статус" htmlFor="object-active">
            <SelectInput
              id="object-active"
              value={filters.isActive}
              onChange={(event) => updateFilters({ isActive: event.target.value as WorkObjectFilters["isActive"] })}
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
      {objects.isLoading ? <LoadingState variant="table" /> : null}
      {objects.isError ? <ErrorState error={objects.error} onRetry={() => void objects.refetch()} /> : null}
      {objects.data && objects.data.length === 0 ? <EmptyState title="Объекты не найдены" /> : null}
      {objects.data && objects.data.length > 0 ? (
        <>
          <div className="space-y-3 md:hidden">
            {objects.data.map((workObject) => (
              <article key={workObject.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                <div className="flex items-start justify-between gap-2">
                  <h2 className="font-medium">{workObject.name}</h2>
                  <ActiveBadge active={workObject.is_active} />
                </div>
                <ObjectFacts workObject={workObject} />
                {isAdmin ? <ObjectActions workObject={workObject} pending={activationMutation.isPending} onEdit={() => { setFormError(null); setEditing(workObject); }} onToggle={() => workObject.is_active ? setDeactivateTarget(workObject) : activationMutation.mutate(workObject)} /> : null}
              </article>
            ))}
          </div>
          <div className="hidden overflow-x-auto md:block">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-2 py-2 font-medium">Название</th>
                  <th className="px-2 py-2 font-medium">Начало</th>
                  <th className="px-2 py-2 font-medium">До</th>
                  <th className="px-2 py-2 font-medium">После</th>
                  <th className="px-2 py-2 font-medium">Часовой пояс</th>
                  <th className="px-2 py-2 font-medium">Статус</th>
                  {isAdmin ? <th className="px-2 py-2 font-medium">Действия</th> : null}
                </tr>
              </thead>
              <tbody>
                {objects.data.map((workObject) => (
                  <tr key={workObject.id} className="border-b border-slate-100">
                    <td className="px-2 py-2">{workObject.name}</td>
                    <td className="px-2 py-2">{formatTime(workObject.shift_start_time)}</td>
                    <td className="px-2 py-2">{workObject.checkin_before_minutes} мин</td>
                    <td className="px-2 py-2">{workObject.checkin_after_minutes} мин</td>
                    <td className="px-2 py-2">{workObject.timezone}</td>
                    <td className="px-2 py-2"><ActiveBadge active={workObject.is_active} /></td>
                    {isAdmin ? (
                      <td className="px-2 py-2">
                        <ObjectActions workObject={workObject} pending={activationMutation.isPending} onEdit={() => { setFormError(null); setEditing(workObject); }} onToggle={() => workObject.is_active ? setDeactivateTarget(workObject) : activationMutation.mutate(workObject)} />
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <PaginationControls offset={filters.offset} limit={PAGE_SIZE} count={objects.data.length} onOffsetChange={(offset) => updateFilters({ offset })} />
        </>
      ) : null}
      <Modal title={editing === "create" ? "Новый объект" : "Редактирование объекта"} open={editing !== null} onClose={() => setEditing(null)}>
        {editing !== null ? (
          <WorkObjectForm
            key={editing === "create" ? "create" : editing.id}
            workObject={editing === "create" ? null : editing}
            pending={saveMutation.isPending}
            error={formError}
            onCancel={() => setEditing(null)}
            onSubmit={(data) => saveMutation.mutate(data)}
          />
        ) : null}
      </Modal>
      <Modal title="Деактивировать объект?" open={deactivateTarget !== null} onClose={() => setDeactivateTarget(null)}>
        <p className="text-sm text-slate-600">{deactivateTarget?.name} больше не будет доступен для новых смен.</p>
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

function ObjectFacts({ workObject }: { workObject: WorkObject }) {
  return (
    <dl className="mt-2 space-y-1 text-xs text-slate-600">
      <div>Начало смены: {formatTime(workObject.shift_start_time)}</div>
      <div>Допуск до: {workObject.checkin_before_minutes} мин</div>
      <div>Допуск после: {workObject.checkin_after_minutes} мин</div>
      <div>Timezone: {workObject.timezone}</div>
    </dl>
  );
}

function ObjectActions({
  workObject,
  pending,
  onEdit,
  onToggle,
}: {
  workObject: WorkObject;
  pending: boolean;
  onEdit: () => void;
  onToggle: () => void;
}) {
  return (
    <div className="mt-3 flex flex-col gap-2 sm:mt-0 sm:flex-row">
      <button type="button" className={buttonClass.secondary} onClick={onEdit}>
        Изменить
      </button>
      <button type="button" className={workObject.is_active ? buttonClass.danger : buttonClass.primary} disabled={pending} onClick={onToggle}>
        {workObject.is_active ? "Деактивировать" : "Активировать"}
      </button>
    </div>
  );
}
