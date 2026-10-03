import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { confirmReview, rejectReview } from "../api/reviews.ts";
import { Field, SelectInput, TextInput } from "./Field.tsx";
import { MessagePhoto } from "./MessagePhoto.tsx";
import { Modal } from "./Modal.tsx";
import { StatusBadge } from "./StatusBadge.tsx";
import { useEmployees, useWorkObjects } from "../hooks/useDirectories.ts";
import { getApiErrorMessage } from "../lib/apiErrorMessage.ts";
import { formatDate, formatDateTime, formatMessageReason, formatTelegramUser, messagePreview } from "../lib/format.ts";
import { queryClient } from "../lib/queryClient.ts";
import { buttonClass } from "../lib/ui.ts";
import { ApiError } from "../types/api.ts";
import type { ReviewMessage } from "../types/message.ts";

async function refreshAfterReview() {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["reviews"] }),
    queryClient.invalidateQueries({ queryKey: ["messages"] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
    queryClient.invalidateQueries({ queryKey: ["shifts"] }),
    queryClient.invalidateQueries({ queryKey: ["message"] }),
    queryClient.invalidateQueries({ queryKey: ["message-logs"] }),
    queryClient.invalidateQueries({ queryKey: ["message-photo"] }),
  ]);
}

export function ReviewDetail({
  message,
  onBack,
  onDone,
}: {
  message: ReviewMessage;
  onBack: () => void;
  onDone: (notice: string) => void;
}) {
  const employees = useEmployees();
  const workObjects = useWorkObjects();
  const [employeeId, setEmployeeId] = useState(message.employee_id?.toString() ?? "");
  const [objectId, setObjectId] = useState(message.object_id?.toString() ?? "");
  const [shiftDate, setShiftDate] = useState(message.shift_date ?? "");
  const [comment, setComment] = useState("");
  const [rejectOpen, setRejectOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const confirmMutation = useMutation({
    mutationFn: () =>
      confirmReview(message.id, {
        employee_id: Number(employeeId),
        object_id: Number(objectId),
        shift_date: shiftDate,
      }),
    onSuccess: async () => {
      await refreshAfterReview();
      onDone("Смена подтверждена");
    },
    onError: async (error) => {
      setFormError(getApiErrorMessage(error));
      if (error instanceof ApiError && error.status === 409) {
        await refreshAfterReview();
        onDone(getApiErrorMessage(error));
      }
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => rejectReview(message.id, { comment: comment.trim() || null }),
    onSuccess: async () => {
      setRejectOpen(false);
      await refreshAfterReview();
      onDone("Сообщение отклонено");
    },
    onError: async (error) => {
      setFormError(getApiErrorMessage(error));
      if (error instanceof ApiError && error.status === 409) {
        setRejectOpen(false);
        await refreshAfterReview();
        onDone(getApiErrorMessage(error));
      }
    },
  });

  const pending = confirmMutation.isPending || rejectMutation.isPending;

  function submitConfirm() {
    if (!employeeId || !objectId || !shiftDate) {
      setFormError("Выберите сотрудника, объект и дату смены");
      return;
    }
    setFormError(null);
    confirmMutation.mutate();
  }

  return (
    <div className="space-y-4">
      <button type="button" className={`${buttonClass.secondary} lg:hidden`} onClick={onBack}>
        Назад
      </button>
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-lg font-semibold">Сообщение {message.id}</h2>
        <StatusBadge status={message.status} />
      </div>
      <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-slate-500">Telegram</dt>
          <dd>{formatTelegramUser(message.telegram_username, message.telegram_user_id)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Причина</dt>
          <dd>{formatMessageReason(message.reason)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Создано в Telegram</dt>
          <dd>{formatDateTime(message.telegram_created_at)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Получено</dt>
          <dd>{formatDateTime(message.created_at)}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-slate-500">Текст</dt>
          <dd className="whitespace-pre-wrap break-words">{messagePreview(message.text, message.caption)}</dd>
        </div>
      </dl>
      <MessagePhoto messageId={message.id} hasPhoto={message.photo_storage_key !== null} />
      <form
        className="space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          submitConfirm();
        }}
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Сотрудник" htmlFor={`review-employee-${message.id}`}>
            <SelectInput
              id={`review-employee-${message.id}`}
              value={employeeId}
              disabled={pending}
              onChange={(event) => setEmployeeId(event.target.value)}
            >
              <option value="">Не выбран</option>
              {message.employee_id !== null && !(employees.data ?? []).some((item) => item.id === message.employee_id) ? (
                <option value={message.employee_id}>Сотрудник #{message.employee_id}</option>
              ) : null}
              {(employees.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.full_name}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Объект" htmlFor={`review-object-${message.id}`}>
            <SelectInput
              id={`review-object-${message.id}`}
              value={objectId}
              disabled={pending}
              onChange={(event) => setObjectId(event.target.value)}
            >
              <option value="">Не выбран</option>
              {message.object_id !== null && !(workObjects.data ?? []).some((item) => item.id === message.object_id) ? (
                <option value={message.object_id}>Объект #{message.object_id}</option>
              ) : null}
              {(workObjects.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Дата смены" htmlFor={`review-date-${message.id}`}>
            <TextInput
              id={`review-date-${message.id}`}
              type="date"
              value={shiftDate}
              disabled={pending}
              onChange={(event) => setShiftDate(event.target.value)}
            />
          </Field>
        </div>
        {formError ? (
          <p className="text-sm text-rose-700" role="alert">
            {formError}
          </p>
        ) : null}
        <div className="flex flex-col gap-2 sm:flex-row">
          <button type="submit" className={`${buttonClass.primary} w-full sm:w-auto`} disabled={pending}>
            {confirmMutation.isPending ? "Подтверждение…" : "Подтвердить"}
          </button>
          <button
            type="button"
            className={`${buttonClass.danger} w-full sm:w-auto`}
            disabled={pending}
            onClick={() => setRejectOpen(true)}
          >
            Отклонить
          </button>
        </div>
      </form>
      <Modal title="Отклонить сообщение" open={rejectOpen} onClose={() => setRejectOpen(false)}>
        <Field label="Комментарий" htmlFor={`reject-comment-${message.id}`}>
          <textarea
            id={`reject-comment-${message.id}`}
            className="min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={comment}
            disabled={pending}
            onChange={(event) => setComment(event.target.value)}
          />
        </Field>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            className={`${buttonClass.danger} w-full sm:w-auto`}
            disabled={pending}
            onClick={() => rejectMutation.mutate()}
          >
            {rejectMutation.isPending ? "Отклонение…" : "Отклонить"}
          </button>
          <button type="button" className={buttonClass.secondary} disabled={pending} onClick={() => setRejectOpen(false)}>
            Отмена
          </button>
        </div>
      </Modal>
      <p className="text-xs text-slate-500">Текущая дата смены: {formatDate(message.shift_date)}</p>
    </div>
  );
}
