import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { activateUser, createUser, deactivateUser, updateUser } from "../api/users.ts";
import { formatUserRole } from "../auth/roles.ts";
import { ActiveBadge } from "../components/ActiveBadge.tsx";
import { EmptyState } from "../components/EmptyState.tsx";
import { ErrorState } from "../components/ErrorState.tsx";
import { Field, SelectInput } from "../components/Field.tsx";
import { FilterBar } from "../components/FilterBar.tsx";
import { LoadingState } from "../components/LoadingState.tsx";
import { Modal } from "../components/Modal.tsx";
import { PageHeader } from "../components/PageHeader.tsx";
import { PaginationControls } from "../components/PaginationControls.tsx";
import { UserForm } from "../components/UserForm.tsx";
import { useAuth } from "../hooks/useAuth.ts";
import { useUsers } from "../hooks/useAdminLists.ts";
import { getApiErrorMessage } from "../lib/apiErrorMessage.ts";
import { formatDateTime } from "../lib/format.ts";
import { queryClient } from "../lib/queryClient.ts";
import { buttonClass } from "../lib/ui.ts";
import { PAGE_SIZE } from "../types/message.ts";
import type { User, UserFilters, UserRole, UserWrite } from "../types/user.ts";

const EMPTY_FILTERS: UserFilters = { role: "", isActive: "", offset: 0 };
const ROLES: UserRole[] = ["admin", "moderator"];

export function UsersPage() {
  const { user: currentUser, refreshUser } = useAuth();
  const [filters, setFilters] = useState<UserFilters>(EMPTY_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [editing, setEditing] = useState<User | null | "create">(null);
  const [deactivateTarget, setDeactivateTarget] = useState<User | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const users = useUsers(filters);

  function updateFilters(patch: Partial<UserFilters>) {
    setFilters((current) => ({ ...current, ...patch, offset: patch.offset ?? 0 }));
  }

  const saveMutation = useMutation({
    mutationFn: (data: UserWrite) =>
      editing && editing !== "create" ? updateUser(editing.id, data) : createUser(data),
    onSuccess: async (saved) => {
      const wasCreate = editing === "create";
      const editedSelf = currentUser !== null && saved.id === currentUser.id;
      setEditing(null);
      setFormError(null);
      setNotice(wasCreate ? "Пользователь добавлен" : "Пользователь обновлён");
      await queryClient.invalidateQueries({ queryKey: ["users"] });
      if (editedSelf) {
        await refreshUser();
      }
    },
    onError: (error) => setFormError(getApiErrorMessage(error)),
  });

  const activationMutation = useMutation({
    mutationFn: (account: User) => (account.is_active ? deactivateUser(account.id) : activateUser(account.id)),
    onSuccess: async (_result, account) => {
      setDeactivateTarget(null);
      setNotice(account.is_active ? "Пользователь деактивирован" : "Пользователь активирован");
      await queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error) => setNotice(getApiErrorMessage(error)),
  });

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <PageHeader title="Users" description="Учётные записи администраторов и модераторов" />
        <button
          type="button"
          className={`${buttonClass.primary} w-full shrink-0 sm:w-auto`}
          onClick={() => {
            setFormError(null);
            setEditing("create");
          }}
        >
          Добавить пользователя
        </button>
      </div>
      <button type="button" className={`${buttonClass.secondary} mb-3 md:hidden`} onClick={() => setFiltersOpen((open) => !open)}>
        {filtersOpen ? "Скрыть фильтры" : "Фильтры"}
      </button>
      <div className={filtersOpen ? "mb-4 block" : "mb-4 hidden md:block"}>
        <FilterBar>
          <Field label="Роль" htmlFor="user-role-filter">
            <SelectInput
              id="user-role-filter"
              value={filters.role}
              onChange={(event) => updateFilters({ role: event.target.value as UserFilters["role"] })}
            >
              <option value="">Все</option>
              {ROLES.map((role) => (
                <option key={role} value={role}>
                  {formatUserRole(role)}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Статус" htmlFor="user-active-filter">
            <SelectInput
              id="user-active-filter"
              value={filters.isActive}
              onChange={(event) => updateFilters({ isActive: event.target.value as UserFilters["isActive"] })}
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
      {users.isLoading ? <LoadingState variant="table" /> : null}
      {users.isError ? <ErrorState error={users.error} onRetry={() => void users.refetch()} /> : null}
      {users.data && users.data.length === 0 ? <EmptyState title="Пользователи не найдены" /> : null}
      {users.data && users.data.length > 0 ? (
        <>
          <div className="space-y-3 md:hidden">
            {users.data.map((account) => (
              <article key={account.id} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-sm font-medium">{account.full_name}</h2>
                    <p className="text-xs text-slate-500">{account.email}</p>
                  </div>
                  <ActiveBadge active={account.is_active} />
                </div>
                <p className="mt-2 text-xs text-slate-500">{formatUserRole(account.role)} · {formatDateTime(account.created_at)}</p>
                <UserActions
                  account={account}
                  currentUserId={currentUser?.id ?? null}
                  pending={activationMutation.isPending}
                  onEdit={() => {
                    setFormError(null);
                    setEditing(account);
                  }}
                  onToggle={() => (account.is_active ? setDeactivateTarget(account) : activationMutation.mutate(account))}
                />
              </article>
            ))}
          </div>
          <div className="hidden overflow-x-auto md:block">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-2 py-2 font-medium">Имя</th>
                  <th className="px-2 py-2 font-medium">Email</th>
                  <th className="px-2 py-2 font-medium">Роль</th>
                  <th className="px-2 py-2 font-medium">Статус</th>
                  <th className="px-2 py-2 font-medium">Создан</th>
                  <th className="px-2 py-2 font-medium">Действия</th>
                </tr>
              </thead>
              <tbody>
                {users.data.map((account) => (
                  <tr key={account.id} className="border-b border-slate-100">
                    <td className="px-2 py-2">{account.full_name}</td>
                    <td className="px-2 py-2">{account.email}</td>
                    <td className="px-2 py-2">{formatUserRole(account.role)}</td>
                    <td className="px-2 py-2"><ActiveBadge active={account.is_active} /></td>
                    <td className="px-2 py-2">{formatDateTime(account.created_at)}</td>
                    <td className="px-2 py-2">
                      <UserActions
                        account={account}
                        currentUserId={currentUser?.id ?? null}
                        pending={activationMutation.isPending}
                        onEdit={() => {
                          setFormError(null);
                          setEditing(account);
                        }}
                        onToggle={() => (account.is_active ? setDeactivateTarget(account) : activationMutation.mutate(account))}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <PaginationControls offset={filters.offset} limit={PAGE_SIZE} count={users.data.length} onOffsetChange={(offset) => updateFilters({ offset })} />
        </>
      ) : null}
      <Modal title={editing === "create" ? "Новый пользователь" : "Редактирование пользователя"} open={editing !== null} onClose={() => setEditing(null)}>
        {editing !== null ? (
          <UserForm
            key={editing === "create" ? "create" : editing.id}
            account={editing === "create" ? null : editing}
            currentUserId={currentUser?.id ?? null}
            pending={saveMutation.isPending}
            error={formError}
            onCancel={() => setEditing(null)}
            onSubmit={(data) => saveMutation.mutate(data)}
          />
        ) : null}
      </Modal>
      <Modal title="Деактивировать пользователя?" open={deactivateTarget !== null} onClose={() => setDeactivateTarget(null)}>
        <p className="text-sm text-slate-600">{deactivateTarget?.full_name} не сможет войти, пока учётную запись снова не включат.</p>
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

function UserActions({
  account,
  currentUserId,
  pending,
  onEdit,
  onToggle,
}: {
  account: User;
  currentUserId: number | null;
  pending: boolean;
  onEdit: () => void;
  onToggle: () => void;
}) {
  const isSelf = account.id === currentUserId;
  return (
    <div className="mt-3 flex flex-col gap-2 sm:mt-0 sm:flex-row">
      <button type="button" className={buttonClass.secondary} onClick={onEdit}>
        Изменить
      </button>
      {isSelf && account.is_active ? null : (
        <button type="button" className={account.is_active ? buttonClass.danger : buttonClass.primary} disabled={pending} onClick={onToggle}>
          {account.is_active ? "Деактивировать" : "Активировать"}
        </button>
      )}
    </div>
  );
}
