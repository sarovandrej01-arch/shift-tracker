import { ErrorState } from "./ErrorState.tsx";
import { LoadingState } from "./LoadingState.tsx";
import { MessagePhoto } from "./MessagePhoto.tsx";
import { StatusBadge } from "./StatusBadge.tsx";
import { useMessageDetail, useMessageLogs } from "../hooks/useMessages.ts";
import {
  formatDate,
  formatDateTime,
  formatMessageReason,
  formatProcessingAction,
  formatTelegramUser,
  messagePreview,
} from "../lib/format.ts";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="break-words">{value}</dd>
    </div>
  );
}

export function MessageDetail({ messageId }: { messageId: number }) {
  const detail = useMessageDetail(messageId);
  const logs = useMessageLogs(messageId);

  if (detail.isLoading) {
    return <LoadingState />;
  }
  if (detail.isError) {
    return <ErrorState error={detail.error} onRetry={() => void detail.refetch()} />;
  }
  if (!detail.data) {
    return null;
  }

  const message = detail.data;

  return (
    <div className="space-y-5 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge status={message.status} />
        <span className="text-slate-500">{formatMessageReason(message.reason)}</span>
      </div>
      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Row label="ID" value={String(message.id)} />
        <Row label="Telegram message" value={String(message.telegram_message_id)} />
        <Row label="Chat" value={String(message.telegram_chat_id)} />
        <Row label="Пользователь" value={formatTelegramUser(message.telegram_username, message.telegram_user_id)} />
        <Row label="Telegram user ID" value={message.telegram_user_id === null ? "—" : String(message.telegram_user_id)} />
        <Row label="Создано в Telegram" value={formatDateTime(message.telegram_created_at)} />
        <Row label="Получено" value={formatDateTime(message.created_at)} />
        <Row label="Обновлено" value={formatDateTime(message.updated_at)} />
        <Row label="Дата смены" value={formatDate(message.shift_date)} />
        <div className="sm:col-span-2">
          <dt className="text-slate-500">Текст</dt>
          <dd className="whitespace-pre-wrap break-words">{messagePreview(message.text, message.caption)}</dd>
        </div>
      </dl>
      <section>
        <h3 className="mb-2 font-semibold">Связи</h3>
        <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Row
            label="Сотрудник"
            value={message.employee ? `${message.employee.full_name} · ${message.employee.personnel_number}` : "—"}
          />
          <Row label="Объект" value={message.work_object?.name ?? "—"} />
          <Row
            label="Смена"
            value={
              message.shift
                ? `${formatDate(message.shift.shift_date)} · ${message.shift.confirmed_manually ? "вручную" : "автоматически"}`
                : "—"
            }
          />
        </dl>
      </section>
      <section>
        <h3 className="mb-2 font-semibold">Фото</h3>
        <MessagePhoto messageId={message.id} hasPhoto={message.photo_storage_key !== null} />
      </section>
      <section>
        <h3 className="mb-2 font-semibold">История обработки</h3>
        {logs.isLoading ? <LoadingState /> : null}
        {logs.isError ? <ErrorState error={logs.error} onRetry={() => void logs.refetch()} /> : null}
        {logs.data && logs.data.length === 0 ? <p className="text-slate-500">Записей нет</p> : null}
        {logs.data && logs.data.length > 0 ? (
          <ol className="space-y-3 border-l border-slate-200 pl-4">
            {logs.data.map((log) => (
              <li key={log.id}>
                <p className="font-medium">{formatProcessingAction(log.action)}</p>
                <p className="text-xs text-slate-500">
                  {formatDateTime(log.created_at)}
                  {log.user_id !== null ? ` · пользователь ${log.user_id}` : ""}
                </p>
                {log.details ? <p className="mt-1 whitespace-pre-wrap break-words text-slate-700">{log.details}</p> : null}
              </li>
            ))}
          </ol>
        ) : null}
      </section>
    </div>
  );
}
