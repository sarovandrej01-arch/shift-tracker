import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import {
  activateTelegramGroup,
  createTelegramGroup,
  deactivateTelegramGroup,
  updateTelegramGroup,
} from "../api/telegramGroups.ts";
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
import { TelegramGroupForm } from "../components/TelegramGroupForm.tsx";
import { useAuth } from "../hooks/useAuth.ts";
import { useTelegramGroups } from "../hooks/useAdminLists.ts";
import { useWorkObjects } from "../hooks/useDirectories.ts";
import { getApiErrorMessage } from "../lib/apiErrorMessage.ts";
import { formatDateTime } from "../lib/format.ts";
import { queryClient } from "../lib/queryClient.ts";
import { buttonClass } from "../lib/ui.ts";
import { PAGE_SIZE } from "../types/message.ts";
import type { TelegramGroup, TelegramGroupFilters, TelegramGroupWrite } from "../types/telegramGroup.ts";

const EMPTY_FILTERS: TelegramGroupFilters = { isActive: "", objectId: "", search: "", offset: 0 };

export function TelegramGroupsPage() {
  const { user } = useAuth();
  const isAdmin = canAccessAdmin(user);
  const [filters, setFilters] = useState<TelegramGroupFilters>(EMPTY_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [editing, setEditing] = useState<TelegramGroup | null | "create">(null);
  const [deactivateTarget, setDeactivateTarget] = useState<TelegramGroup | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const groups = useTelegramGroups(filters);
  const workObjects = useWorkObjects();
  const objectNames = new Map((workObjects.data ?? []).map((item) => [item.id, item.name]));

  function updateFilters(patch: Partial<TelegramGroupFilters>) {
    setFilters((current) => ({ ...current, ...patch, offset: patch.offset ?? 0 }));
  }

  async function refresh() {
    await queryClient.invalidateQueries({ queryKey: ["telegram-groups"] });
  }

  const saveMutation = useMutation({
    mutationFn: (data: TelegramGroupWrite) =>
      editing && editing !== "create" ? updateTelegramGroup(editing.id, data) : createTelegramGroup(data),
    onSuccess: async () => {
      const wasCreate = editing === "create";
      setEditing(null);
      setFormError(null);
      setNotice(wasCreate ? "Группа добавлена" : "Группа обновлена");
      await refresh();
    },
    onError: (error) => setFormError(getApiErrorMessage(error)),
  });

  const activationMutation = useMutation({
    mutationFn: (group: TelegramGroup) =>
      group.is_active ? deactivateTelegramGroup(group.id) : activateTelegramGroup(group.id),
    onSuccess: async (_result, group) => {
      setDeactivateTarget(null);
      setNotice(group.is_active ? "Группа деактивирована" : "Группа активирована");
      await refresh();
    },
    onError: (error) => setNotice(getApiErrorMessage(error)),
  });

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <PageHeader title="Telegram Groups" description="Чаты, из которых приходят отметки" />
        {isAdmin ? (
          <button
            type="button"
            className={`${buttonClass.primary} w-full shrink-0 sm:w-auto`}
            onClick={() => {
              setFormError(null);
              setEditing("create");
            }}
          >
            Добавить группу
          </button>
        ) : null}
      </div>
      <button type="button" className={`${buttonClass.secondary} mb-3 md:hidden`} onClick={() => setFiltersOpen((open) => !open)}>
        {filtersOpen ? "Скрыть фильтры" : "Фильтры"}
      </button>
      <div className={filtersOpen ? "mb-4 block" : "mb-4 hidden md:block"}>
        <FilterBar>
          <Field label="Поиск" htmlFor="group-search">
            <TextInput id="group-search" value={filters.search} placeholder="Название" onChange={(event) => updateFilters({ search: event.target.value })} />
          </Field>
          <Field label="Объект" htmlFor="group-object-filter">
            <SelectInput id="group-object-filter" value={filters.objectId} onChange={(event) => updateFilters({ objectId: event.target.value })}>
              <option value="">Все</option>
              {(workObjects.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Статус" htmlFor="group-active">
            <SelectInput
              id="group-active"
              value={filters.isActive}
              onChange={(event) => updateFilters({ isActive: event.target.value as TelegramGroupFilters["isActive"] })}
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
      {groups.isLoading ? <LoadingState variant="table" /> : null}
      {groups.isError ? <ErrorState error={groups.error} onRetry={() => void groups.refetch()} /> : null}
      {groups.data && groups.data.length === 0 ? <EmptyState title="Группы не найдены" /> : null}
      {groups.data && groups.data.length > 0 ? (
        <>
          <div className="space-y-3 md:hidden">
            {groups.data.map((group) => (
              <article key={group.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="font-medium">{group.name}</h2>
                    <p className="text-xs text-slate-500">#{group.id} · {group.telegram_chat_id}</p>
                  </div>
                  <ActiveBadge active={group.is_active} />
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  {objectNames.get(group.object_id) ?? `Объект #${group.object_id}`} · {formatDateTime(group.created_at)}
                </p>
                {isAdmin ? (
                  <GroupActions
                    group={group}
                    pending={activationMutation.isPending}
                    onEdit={() => {
                      setFormError(null);
                      setEditing(group);
                    }}
                    onToggle={() => (group.is_active ? setDeactivateTarget(group) : activationMutation.mutate(group))}
                  />
                ) : null}
              </article>
            ))}
          </div>
          <div className="hidden overflow-x-auto md:block">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-2 py-2 font-medium">ID</th>
                  <th className="px-2 py-2 font-medium">Название</th>
                  <th className="px-2 py-2 font-medium">Chat ID</th>
                  <th className="px-2 py-2 font-medium">Объект</th>
                  <th className="px-2 py-2 font-medium">Статус</th>
                  <th className="px-2 py-2 font-medium">Создана</th>
                  {isAdmin ? <th className="px-2 py-2 font-medium">Действия</th> : null}
                </tr>
              </thead>
              <tbody>
                {groups.data.map((group) => (
                  <tr key={group.id} className="border-b border-slate-100">
                    <td className="px-2 py-2">{group.id}</td>
                    <td className="px-2 py-2">{group.name}</td>
                    <td className="px-2 py-2">{group.telegram_chat_id}</td>
                    <td className="px-2 py-2">{objectNames.get(group.object_id) ?? `#${group.object_id}`}</td>
                    <td className="px-2 py-2"><ActiveBadge active={group.is_active} /></td>
                    <td className="px-2 py-2">{formatDateTime(group.created_at)}</td>
                    {isAdmin ? (
                      <td className="px-2 py-2">
                        <GroupActions
                          group={group}
                          pending={activationMutation.isPending}
                          onEdit={() => {
                            setFormError(null);
                            setEditing(group);
                          }}
                          onToggle={() => (group.is_active ? setDeactivateTarget(group) : activationMutation.mutate(group))}
                        />
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <PaginationControls offset={filters.offset} limit={PAGE_SIZE} count={groups.data.length} onOffsetChange={(offset) => updateFilters({ offset })} />
        </>
      ) : null}
      <Modal title={editing === "create" ? "Новая группа" : "Редактирование группы"} open={editing !== null} onClose={() => setEditing(null)}>
        {editing !== null ? (
          <TelegramGroupForm
            key={editing === "create" ? "create" : editing.id}
            group={editing === "create" ? null : editing}
            workObjects={workObjects.data ?? []}
            pending={saveMutation.isPending}
            error={formError}
            onCancel={() => setEditing(null)}
            onSubmit={(data) => saveMutation.mutate(data)}
          />
        ) : null}
      </Modal>
      <Modal title="Деактивировать группу?" open={deactivateTarget !== null} onClose={() => setDeactivateTarget(null)}>
        <p className="text-sm text-slate-600">{deactivateTarget?.name} перестанет приниматься, пока группу снова не включат.</p>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            className={`${buttonClass.danger} w-full sm:w-auto`}
            disabled={activationMutation.isPending}
            onClick={() => deactivateTarget && activationMutation.mutate(deactivateTarget)}
          >
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

function GroupActions({
  group,
  pending,
  onEdit,
  onToggle,
}: {
  group: TelegramGroup;
  pending: boolean;
  onEdit: () => void;
  onToggle: () => void;
}) {
  return (
    <div className="mt-3 flex flex-col gap-2 sm:mt-0 sm:flex-row">
      <button type="button" className={buttonClass.secondary} onClick={onEdit}>
        Изменить
      </button>
      <button type="button" className={group.is_active ? buttonClass.danger : buttonClass.primary} disabled={pending} onClick={onToggle}>
        {group.is_active ? "Деактивировать" : "Активировать"}
      </button>
    </div>
  );
}
