import { useState } from "react";

import { EmptyState } from "../components/EmptyState.tsx";
import { ErrorState } from "../components/ErrorState.tsx";
import { Field, SelectInput, TextInput } from "../components/Field.tsx";
import { FilterBar } from "../components/FilterBar.tsx";
import { LoadingState } from "../components/LoadingState.tsx";
import { MessageDetail } from "../components/MessageDetail.tsx";
import { Modal } from "../components/Modal.tsx";
import { PageHeader } from "../components/PageHeader.tsx";
import { PaginationControls } from "../components/PaginationControls.tsx";
import { StatusBadge } from "../components/StatusBadge.tsx";
import { useEmployees, useWorkObjects } from "../hooks/useDirectories.ts";
import { useMessages } from "../hooks/useMessages.ts";
import { formatDate, formatDateTime, formatMessageReason, formatMessageStatus, formatTelegramUser, messagePreview } from "../lib/format.ts";
import { buttonClass } from "../lib/ui.ts";
import type { MessageFilters, MessageReason, MessageStatus, TelegramMessage } from "../types/message.ts";
import { PAGE_SIZE } from "../types/message.ts";

const STATUSES: MessageStatus[] = ["new", "processing", "accepted", "review", "rejected", "duplicate", "error"];
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

const EMPTY_FILTERS: MessageFilters = {
  status: "",
  reason: "",
  employeeId: "",
  objectId: "",
  dateFrom: "",
  dateTo: "",
  telegramChatId: "",
  telegramUserId: "",
  shiftDateFrom: "",
  shiftDateTo: "",
  offset: 0,
};

export function MessagesPage() {
  const [filters, setFilters] = useState<MessageFilters>(EMPTY_FILTERS);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const messages = useMessages(filters);
  const employees = useEmployees();
  const workObjects = useWorkObjects();
  const employeeNames = new Map((employees.data ?? []).map((item) => [item.id, item.full_name]));
  const objectNames = new Map((workObjects.data ?? []).map((item) => [item.id, item.name]));

  function updateFilters(patch: Partial<MessageFilters>) {
    setFilters((current) => ({ ...current, ...patch, offset: patch.offset ?? 0 }));
  }

  function relationLabel(message: TelegramMessage): string {
    const employee = message.employee_id
      ? (employeeNames.get(message.employee_id) ?? `#${message.employee_id}`)
      : "—";
    const object = message.object_id ? (objectNames.get(message.object_id) ?? `#${message.object_id}`) : "—";
    return `${employee} · ${object}`;
  }

  return (
    <div>
      <PageHeader title="Messages" description="Все входящие сообщения" />
      <button
        type="button"
        className={`${buttonClass.secondary} mb-3 md:hidden`}
        onClick={() => setFiltersOpen((open) => !open)}
      >
        {filtersOpen ? "Скрыть фильтры" : "Фильтры"}
      </button>
      <div className={filtersOpen ? "mb-4 space-y-3" : "mb-4 hidden space-y-3 md:block"}>
        <FilterBar>
          <Field label="Статус" htmlFor="message-status">
            <SelectInput id="message-status" value={filters.status} onChange={(event) => updateFilters({ status: event.target.value })}>
              <option value="">Все</option>
              {STATUSES.map((status) => (
                <option key={status} value={status}>
                  {formatMessageStatus(status)}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Причина" htmlFor="message-reason">
            <SelectInput id="message-reason" value={filters.reason} onChange={(event) => updateFilters({ reason: event.target.value })}>
              <option value="">Все</option>
              {REASONS.map((reason) => (
                <option key={reason} value={reason}>
                  {formatMessageReason(reason)}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Сотрудник" htmlFor="message-employee">
            <SelectInput
              id="message-employee"
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
          <Field label="Объект" htmlFor="message-object">
            <SelectInput id="message-object" value={filters.objectId} onChange={(event) => updateFilters({ objectId: event.target.value })}>
              <option value="">Все</option>
              {(workObjects.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Дата с" htmlFor="message-date-from">
            <TextInput id="message-date-from" type="date" value={filters.dateFrom} onChange={(event) => updateFilters({ dateFrom: event.target.value })} />
          </Field>
          <Field label="Дата по" htmlFor="message-date-to">
            <TextInput id="message-date-to" type="date" value={filters.dateTo} onChange={(event) => updateFilters({ dateTo: event.target.value })} />
          </Field>
          <div className="flex items-end">
            <button type="button" className={`${buttonClass.secondary} w-full`} onClick={() => updateFilters(EMPTY_FILTERS)}>
              Сбросить фильтры
            </button>
          </div>
        </FilterBar>
        <button type="button" className={buttonClass.secondary} onClick={() => setAdvancedOpen((open) => !open)}>
          {advancedOpen ? "Скрыть дополнительные фильтры" : "Дополнительные фильтры"}
        </button>
        {advancedOpen ? (
          <FilterBar>
            <Field label="Telegram chat ID" htmlFor="message-chat">
              <TextInput
                id="message-chat"
                inputMode="numeric"
                value={filters.telegramChatId}
                onChange={(event) => updateFilters({ telegramChatId: event.target.value })}
              />
            </Field>
            <Field label="Telegram user ID" htmlFor="message-user">
              <TextInput
                id="message-user"
                inputMode="numeric"
                value={filters.telegramUserId}
                onChange={(event) => updateFilters({ telegramUserId: event.target.value })}
              />
            </Field>
            <Field label="Смена с" htmlFor="shift-date-from">
              <TextInput
                id="shift-date-from"
                type="date"
                value={filters.shiftDateFrom}
                onChange={(event) => updateFilters({ shiftDateFrom: event.target.value })}
              />
            </Field>
            <Field label="Смена по" htmlFor="shift-date-to">
              <TextInput
                id="shift-date-to"
                type="date"
                value={filters.shiftDateTo}
                onChange={(event) => updateFilters({ shiftDateTo: event.target.value })}
              />
            </Field>
          </FilterBar>
        ) : null}
      </div>
      {messages.isLoading ? <LoadingState variant="table" /> : null}
      {messages.isError ? <ErrorState error={messages.error} onRetry={() => void messages.refetch()} /> : null}
      {messages.data && messages.data.length === 0 ? <EmptyState title="Сообщения не найдены" /> : null}
      {messages.data && messages.data.length > 0 ? (
        <>
          <div className="space-y-3 md:hidden">
            {messages.data.map((item) => (
              <button
                key={item.id}
                type="button"
                className="w-full rounded-lg border border-slate-200 p-3 text-left"
                onClick={() => setSelectedId(item.id)}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">#{item.id}</span>
                  <StatusBadge status={item.status} />
                </div>
                <p className="mt-2 line-clamp-2 text-sm">{messagePreview(item.text, item.caption)}</p>
                <p className="mt-2 text-xs text-slate-500">{formatTelegramUser(item.telegram_username, item.telegram_user_id)}</p>
                <p className="mt-1 text-xs text-slate-500">{formatMessageReason(item.reason)}</p>
                <p className="mt-1 text-xs text-slate-500">{formatDateTime(item.created_at)}</p>
                <p className="mt-1 text-xs text-slate-500">{relationLabel(item)}</p>
              </button>
            ))}
          </div>
          <div className="hidden overflow-x-auto md:block">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-2 py-2 font-medium">ID</th>
                  <th className="px-2 py-2 font-medium">Telegram</th>
                  <th className="px-2 py-2 font-medium">Текст</th>
                  <th className="px-2 py-2 font-medium">Статус</th>
                  <th className="px-2 py-2 font-medium">Причина</th>
                  <th className="px-2 py-2 font-medium">Сотрудник</th>
                  <th className="px-2 py-2 font-medium">Объект</th>
                  <th className="px-2 py-2 font-medium">Смена</th>
                  <th className="px-2 py-2 font-medium">Получено</th>
                </tr>
              </thead>
              <tbody>
                {messages.data.map((item) => (
                  <tr
                    key={item.id}
                    tabIndex={0}
                    className="cursor-pointer border-b border-slate-100 hover:bg-slate-50"
                    onClick={() => setSelectedId(item.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setSelectedId(item.id);
                      }
                    }}
                  >
                    <td className="px-2 py-2">{item.id}</td>
                    <td className="px-2 py-2">{formatTelegramUser(item.telegram_username, item.telegram_user_id)}</td>
                    <td className="max-w-xs truncate px-2 py-2">{messagePreview(item.text, item.caption)}</td>
                    <td className="px-2 py-2">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-2 py-2">{formatMessageReason(item.reason)}</td>
                    <td className="px-2 py-2">
                      {item.employee_id ? (employeeNames.get(item.employee_id) ?? `#${item.employee_id}`) : "—"}
                    </td>
                    <td className="px-2 py-2">{item.object_id ? (objectNames.get(item.object_id) ?? `#${item.object_id}`) : "—"}</td>
                    <td className="px-2 py-2">{formatDate(item.shift_date)}</td>
                    <td className="px-2 py-2">{formatDateTime(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <PaginationControls
            offset={filters.offset}
            limit={PAGE_SIZE}
            count={messages.data.length}
            onOffsetChange={(offset) => updateFilters({ offset })}
          />
        </>
      ) : null}
      <Modal title={selectedId === null ? "Сообщение" : `Сообщение ${selectedId}`} open={selectedId !== null} onClose={() => setSelectedId(null)}>
        {selectedId !== null ? <MessageDetail messageId={selectedId} /> : null}
      </Modal>
    </div>
  );
}
